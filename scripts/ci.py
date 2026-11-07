#!/usr/bin/env python3
"""GitHub Actions driver: plan the builds whose inputs changed, run them, publish releases.

State lives in manifest.json on the "current" release. Each plugin and target has the
key of its last build (see build_key in build-target.py), so unchanged builds are skipped.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bt = load("build-target")
# The runner that also runs the source scans, once per plugin.
ANALYSIS_RUNNER = "ubuntu-24.04"


def read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def github_output(**values):
    path = os.getenv("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as output:
            for key, value in values.items():
                output.write(f"{key}={value}\n")


def step_summary(text):
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as output:
            output.write(text + "\n")


def select_targets(spec):
    if spec in ("", "containers"):
        return [name for name, profile in bt.TARGETS.items() if "base" in profile]
    if spec == "all":
        return list(bt.TARGETS)
    names = spec.replace(",", " ").split()
    unknown = [name for name in names if name not in bt.TARGETS]
    if unknown:
        raise SystemExit(f"Unknown targets: {' '.join(unknown)}")
    return names


def resolve(plugin):
    result = subprocess.run(["bash", str(ROOT / "plugins" / plugin / "fetch.sh")],
                            env=dict(os.environ, OPENCPN_FETCH_RESOLVE="1"),
                            capture_output=True, text=True, timeout=120)
    if result.returncode:
        print(f"{plugin}: cannot resolve upstream commit: {result.stderr.strip()}", file=sys.stderr)
        return None
    return result.stdout.strip().splitlines()[-1]


def plan(args):
    state = read_json(args.manifest, {})
    manifest = state.get("plugins", {})
    analyzed = state.get("analyzed", {})
    targets = select_targets(args.targets)
    skipped = [target for target in targets if bt.TARGETS[target]["runner"] in args.skip_runner]
    if skipped:
        print(f"Skipping targets on unavailable runners: {' '.join(skipped)}", file=sys.stderr)
        step_summary(f"Skipped (runner not available): {' '.join(skipped)}\n")
        targets = [target for target in targets if target not in skipped]
    plugins = [name for name in bt.plugins() if args.match.casefold() in name.casefold()]
    with ThreadPoolExecutor(16) as pool:
        commits = dict(zip(plugins, pool.map(resolve, plugins)))

    jobs = {}
    rows = []
    for plugin in plugins:
        commit = commits[plugin]
        if not commit:
            rows.append(f"| {plugin} | - | upstream not reachable |")
            continue
        previous = manifest.get(plugin, {})
        since = next((entry["commit"] for entry in previous.values() if entry.get("status") == "ok"), "")
        wanted = []
        for target in targets:
            if not bt.supports(plugin, target):
                continue
            key = bt.build_key(target, plugin, commit)
            entry = previous.get(target, {})
            known = {entry.get("key")} | (set() if args.retry_failed else {entry.get("failed_key")})
            if args.force or key not in known:
                wanted.append(target)
        if not wanted:
            continue
        rows.append(f"| {plugin} | `{commit[:10]}` | {' '.join(wanted)} |")
        for target in wanted:
            profile = bt.TARGETS[target]
            job = jobs.setdefault((plugin, profile["runner"]), {
                "plugin": plugin, "commit": commit, "since": since, "runner": profile["runner"],
                "qemu": False, "targets": [], "analyze": False,
            })
            job["targets"].append(target)
            job["qemu"] |= bool(profile.get("qemu"))
    # Scan each changed plugin's source once, preferably on the x64 runner.
    for plugin in {job["plugin"] for job in jobs.values()}:
        candidates = [job for job in jobs.values() if job["plugin"] == plugin]
        chosen = next((job for job in candidates if job["runner"] == ANALYSIS_RUNNER), candidates[0])
        chosen["analyze"] = (not args.no_analysis and chosen["runner"].startswith("ubuntu")
                             and (args.force or analyzed.get(plugin) != chosen["commit"]))
    include = [dict(job, targets=" ".join(job["targets"])) for job in jobs.values()]
    if len(include) > 256:
        print(f"{len(include)} jobs exceed the matrix limit; building the first 256. "
              "The rest follow on the next run.", file=sys.stderr)
        include = include[:256]
    matrix = json.dumps({"include": include}, separators=(",", ":"))
    github_output(matrix=matrix, count=len(include))
    step_summary(f"### Build plan: {len(include)} jobs\n\n| Plugin | Commit | Targets |\n|---|---|---|\n"
                 + "\n".join(rows))
    print(matrix)
    return 0


def package_version(tarball):
    try:
        with tarfile.open(tarball, "r:gz") as archive:
            member = next(m for m in archive.getmembers() if Path(m.name).name == "metadata.xml")
            with archive.extractfile(member) as stream:
                metadata = ET.parse(stream).getroot()
        return metadata.findtext("name", "").strip(), metadata.findtext("version", "").strip()
    except (StopIteration, OSError, tarfile.TarError, ET.ParseError):
        return "", ""


def commit_link(url, commit):
    """Markdown link to the upstream commit, so each package points at its exact source."""
    base = url.removesuffix(".git")
    if "gitlab.com" in base:
        path = "/-/commit/"
    elif "bitbucket.org" in base:
        path = "/commits/"
    elif base.startswith("https://"):
        path = "/commit/"
    else:
        return f"`{commit[:10]}`"
    return f"[`{commit[:10]}`]({base}{path}{commit})"


def changes(source, since, commit):
    if not since or since == commit:
        return []
    known = subprocess.run(["git", "-C", str(source), "merge-base", "--is-ancestor", since, commit],
                           capture_output=True).returncode == 0
    if not known:
        return []
    log = subprocess.check_output(["git", "-C", str(source), "log", "--no-merges", "--max-count=30",
                                   "--format=%h %s", f"{since}..{commit}"], text=True)
    return log.splitlines()


def build(args):
    plugin, commit = args.plugin, args.commit
    fetch = subprocess.run(["bash", str(ROOT / "plugins" / plugin / "fetch.sh")],
                           env=dict(os.environ, OPENCPN_FETCH_COMMIT=commit))
    source = ROOT / "repos" / plugin
    head = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True,
                          text=True).stdout.strip()
    result = {"plugin": plugin, "commit": commit, "since": args.since, "targets": {}, "changes": []}
    result["url"] = subprocess.run(["git", "-C", str(source), "remote", "get-url", "origin"],
                                   capture_output=True, text=True).stdout.strip()
    if fetch.returncode or head != commit:
        for target in args.targets:
            result["targets"][target] = {"status": "failed", "error": "fetch failed",
                                         "key": bt.build_key(target, plugin, commit)}
    else:
        result["changes"] = changes(source, args.since, commit)
        for target in args.targets:
            print(f"::group::{target} / {plugin}", flush=True)
            status = subprocess.run([sys.executable, str(ROOT / "scripts" / "build-target.py"),
                                     "build", target, plugin]).returncode
            print("::endgroup::", flush=True)
            files = sorted((ROOT / "dist" / target / plugin).glob("*.tar.gz"))
            name, version = package_version(files[0]) if files else ("", "")
            result["targets"][target] = {
                "status": "ok" if status == 0 and files else "failed",
                "key": bt.build_key(target, plugin, commit),
                "files": [f"{target}/{plugin}/{file.name}" for file in files],
                "name": name, "version": version,
            }
            if status:
                print(f"::error::{plugin} failed for {target}")
        tarballs = [ROOT / "dist" / path for entry in result["targets"].values()
                    if entry["status"] == "ok" for path in entry["files"]]
        if args.analyze or tarballs:
            analyze = load("analyze")
            result["analysis"] = analyze.analyze(plugin, tarballs, source_scans=args.analyze)
    output = ROOT / "dist" / "results"
    output.mkdir(parents=True, exist_ok=True)
    (output / f"{plugin}--{args.runner}.json").write_text(json.dumps(result, indent=2) + "\n")
    return int(any(entry["status"] != "ok" for entry in result["targets"].values()))


def analysis_line(summary):
    if not summary:
        return ""
    parts = []
    cpp = summary.get("cppcheck", {})
    if cpp:
        parts.append("cppcheck " + (cpp["failed"] if "failed" in cpp else
                     ", ".join(f"{count} {kind.replace('_', ' ')}" for kind, count in sorted(cpp.items())) or "clean"))
    for scanner in ("osv", "trivy"):
        found = summary.get(scanner, {})
        if found:
            parts.append(f"{scanner} " + (found["failed"] if "failed" in found else
                         ", ".join(f"{count} {kind}" for kind, count in found.items() if kind != "packages")))
    weak = sorted({item["library"].rsplit("/", 1)[-1] for item in summary.get("hardening", [])
                   if item["relro"] == "none" or not item["nx"] or not item["stack_protector"]})
    hardening = summary.get("hardening")
    if hardening:
        relro = sorted({item["relro"] for item in hardening})
        parts.append(f"ELF: RELRO {'/'.join(relro)}" + (f", weak: {' '.join(weak)}" if weak else ", NX+canary ok"))
    return "; ".join(parts)


def publish(args):
    manifest = read_json(args.manifest, {})
    plugins = manifest.setdefault("plugins", {})
    results = [read_json(path, None) for path in sorted(Path(args.results).glob("results/*.json"))]
    results = [result for result in results if result]
    now = datetime.now(timezone.utc)
    tag = now.strftime("builds-%Y%m%d-%H%M")
    upload, delete = [], set()
    by_plugin = {}
    for result in results:
        merged = by_plugin.setdefault(result["plugin"], {"targets": {}, "changes": result["changes"],
                                                          "commit": result["commit"], "analysis": {},
                                                          "url": result.get("url", "")})
        merged["targets"].update(result["targets"])
        merged["changes"] = merged["changes"] or result["changes"]
        for key, value in (result.get("analysis") or {}).items():
            if key == "hardening":
                merged["analysis"].setdefault("hardening", []).extend(value)
            else:
                merged["analysis"][key] = value

    built, failed = [], []
    for plugin, merged in sorted(by_plugin.items()):
        if merged["analysis"].get("commit"):
            manifest.setdefault("analyzed", {})[plugin] = merged["analysis"]["commit"]
        entries = plugins.setdefault(plugin, {})
        for target, outcome in sorted(merged["targets"].items()):
            previous = entries.get(target, {})
            if outcome["status"] == "ok":
                delete.update(Path(path).name for path in previous.get("files", []))
                entries[target] = {"status": "ok", "key": outcome["key"], "commit": merged["commit"],
                                   "name": outcome["name"], "version": outcome["version"],
                                   "files": outcome["files"], "release": tag,
                                   "built": now.isoformat(timespec="seconds")}
                upload += [str(Path(args.results) / path) for path in outcome["files"]]
                built.append((plugin, target))
            else:
                previous.update(failed_key=outcome["key"], failed_commit=merged["commit"],
                                status=previous.get("status") if previous.get("files") else "failed")
                entries[target] = previous
                failed.append((plugin, target))
    delete -= {Path(path).name for path in upload}

    run = args.run_url
    lines = [f"Automatic build of {len(built)} plugin packages ({now:%Y-%m-%d %H:%M} UTC)."]
    if run:
        lines.append(f"Build logs: {run}")
    lines += ["", "Import a tarball with **Options → Plugins → Import Plugin Tarball** in OpenCPN. "
              "Static analysis and vulnerability scan results are informational. Full reports are in "
              "`analysis.tar.gz`.", ""]
    for plugin, merged in sorted(by_plugin.items()):
        ok = [target for target, outcome in sorted(merged["targets"].items()) if outcome["status"] == "ok"]
        bad = [target for target, outcome in sorted(merged["targets"].items()) if outcome["status"] != "ok"]
        version = next((merged["targets"][target]["version"] for target in ok), "")
        lines.append(f"### {plugin} {version}".rstrip())
        lines.append(f"Source {commit_link(merged['url'], merged['commit'])}. Built: {', '.join(ok) or 'none'}."
                     + (f" **Failed:** {', '.join(bad)}." if bad else ""))
        if merged["changes"]:
            lines += ["", "Upstream changes:", *[f"- {change}" for change in merged["changes"]]]
        line = analysis_line(merged["analysis"])
        if line:
            lines += ["", f"Analysis: {line}"]
        lines.append("")

    current = ["Latest successful build of every plugin and target. Older builds and release "
               "notes are in the dated `builds-*` releases.", "",
               "| Plugin | Version | Targets | Built in |", "|---|---|---|---|"]
    for plugin, entries in sorted(plugins.items()):
        ok = {target: entry for target, entry in entries.items() if entry.get("files")}
        if ok:
            versions = sorted({entry.get("version", "") for entry in ok.values()} - {""})
            releases = sorted({entry["release"] for entry in ok.values()})
            current.append(f"| {plugin} | {' '.join(versions)} | {' '.join(sorted(ok))} | {' '.join(releases)} |")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest["updated"] = now.isoformat(timespec="seconds")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (out / "notes.md").write_text("\n".join(lines) + "\n")
    (out / "current.md").write_text("\n".join(current) + "\n")
    (out / "upload.txt").write_text("".join(f"{path}\n" for path in upload))
    (out / "delete.txt").write_text("".join(f"{name}\n" for name in sorted(delete)))
    analysis = Path(args.results) / "analysis"
    if analysis.is_dir():
        with tarfile.open(out / "analysis.tar.gz", "w:gz") as archive:
            archive.add(analysis, arcname="analysis")
    github_output(tag=tag, built=len(built), failed=len(failed))
    step_summary(f"### Published\n\n{len(built)} packages built, {len(failed)} failed.")
    print(f"{tag}: {len(built)} built, {len(failed)} failed")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("plan", help="emit the matrix of builds whose inputs changed")
    p.add_argument("--manifest", default="state/manifest.json")
    p.add_argument("--targets", default="containers", help="containers, all, or target names")
    p.add_argument("--match", default="", help="plugin directory name filter")
    p.add_argument("--force", action="store_true", help="rebuild even if nothing changed")
    p.add_argument("--retry-failed", action="store_true", help="retry builds that failed with the same inputs")
    p.add_argument("--no-analysis", action="store_true", help="skip the source scans")
    p.add_argument("--skip-runner", action="append", default=[], help="leave out targets on this runner")
    b = commands.add_parser("build", help="fetch one commit and build it for several targets")
    b.add_argument("--plugin", required=True)
    b.add_argument("--commit", required=True)
    b.add_argument("--since", default="")
    b.add_argument("--runner", default="local")
    b.add_argument("--analyze", action="store_true")
    b.add_argument("targets", nargs="+")
    u = commands.add_parser("publish", help="merge build results into the manifest and write release notes")
    u.add_argument("--results", default="dist", help="directory holding the downloaded dist/ artifacts")
    u.add_argument("--manifest", default="state/manifest.json")
    u.add_argument("--out", default="out")
    u.add_argument("--run-url", default="")
    args = parser.parse_args()
    return {"plan": plan, "build": build, "publish": publish}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())

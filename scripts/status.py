#!/usr/bin/env python3
"""Upstream status of every plugin: its newest catalog release, how far the default
branch has moved since, how often it releases, open milestones, and our build.

  status.py [--opencpn 5.12.4] [--manifest manifest.json] [--json] [PLUGIN...]

Without --manifest, the manifest of the "current" GitHub release is used when gh can
read it. GitHub repositories are queried through the API (with GH_TOKEN, GITHUB_TOKEN
or gh's login when available); other forges fall back to the local checkout.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bt = load("build-target")
catalog = load("catalog")
compare = load("compare")


def parse_date(text):
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def days(delta):
    return f"{delta.days} d" if delta.days < 60 else f"{delta.days / 30.4:.0f} mo"


def resolve(plugin):
    result = subprocess.run(["bash", str(ROOT / "plugins" / plugin / "fetch.sh")],
                            env=dict(os.environ, OPENCPN_FETCH_RESOLVE="1"),
                            capture_output=True, text=True, timeout=180)
    commit, _, source = result.stdout.strip().partition(" ")
    return (commit, source) if result.returncode == 0 else ("", result.stderr.strip())


def default_branch(url):
    output = subprocess.run(["git", "ls-remote", "--symref", "--", url, "HEAD"], capture_output=True,
                            text=True, timeout=60).stdout
    match = re.search(r"ref: refs/heads/(\S+)\s+HEAD", output)
    return match.group(1) if match else "HEAD"


def local_history(plugin, base):
    """Commits on the checkout's default branch since base, and base's date, from repos/."""
    source = ROOT / "repos" / plugin
    if not (source / ".git").exists():
        return None, None
    head = "origin/HEAD"
    run = lambda *args: subprocess.run(["git", "-C", str(source), *args], capture_output=True, text=True)
    if run("rev-parse", "--verify", "--quiet", head).returncode:
        head = "HEAD"
    count = run("rev-list", "--count", f"{base}..{head}").stdout.strip()
    date = run("log", "-1", "--format=%cI", base).stdout.strip()
    return (int(count) if count.isdigit() else None), parse_date(date)


def plugin_status(plugin, manifest, opencpn):
    text = (ROOT / "plugins" / plugin / "fetch.sh").read_text(encoding="utf-8")
    url = re.search(r"^url=(\S+)", text, re.M).group(1)
    names = compare.catalog_names(plugin)
    version = catalog.newest_version(names) if names else None
    entries = [entry for entry in catalog.entries(names) if entry.get("version") == version]
    api = next((entry.get("api-version", "") for entry in entries if entry.get("api-version")), "")
    status = {"plugin": plugin, "url": url, "release": version, "api": api,
              "needs_opencpn": catalog.min_opencpn(api) if api else None,
              "catalog_targets": len({(e.get("target"), e.get("target-version")) for e in entries})}
    if opencpn and status["needs_opencpn"]:
        status["opencpn_ok"] = catalog.version_key(opencpn) >= catalog.version_key(status["needs_opencpn"])
    commit, source = resolve(plugin)
    status.update(commit=commit, source=source)

    ref, _ = catalog.release_ref(url, names) if version else (None, "")
    branch = default_branch(url)
    since, released = None, None
    if ref:
        found = catalog.github_api(url, f"compare/{ref}...{branch}")
        if isinstance(found, dict) and "ahead_by" in found:
            since = found["ahead_by"]
            released = parse_date(found.get("merge_base_commit", {}).get("commit", {})
                                  .get("committer", {}).get("date"))
        else:
            since, released = local_history(plugin, ref)
    status.update(release_ref=ref, commits_since_release=since,
                  released=released.isoformat() if released else None)

    releases = catalog.github_api(url, "releases?per_page=12")
    dates = sorted(filter(None, (parse_date(item.get("published_at")) for item in releases
                                 if not item.get("draft"))) if isinstance(releases, list) else [])
    if len(dates) >= 2:
        status["release_interval_days"] = round(statistics.median(
            (later - earlier).days for earlier, later in zip(dates, dates[1:])))
    milestones = catalog.github_api(url, "milestones?state=open&sort=due_on&direction=asc")
    if isinstance(milestones, list):
        due = [(parse_date(item.get("due_on")), item.get("title")) for item in milestones if item.get("due_on")]
        due = sorted(item for item in due if item[0])
        if due:
            status["next_milestone"] = {"title": due[0][1], "due": due[0][0].date().isoformat()}

    built = manifest.get("plugins", {}).get(plugin, {})
    ok = sorted(target for target, entry in built.items() if entry.get("files"))
    failed = sorted(target for target, entry in built.items() if entry.get("failed_key") or entry.get("status") == "failed")
    status["built"] = {"versions": sorted({built[target].get("version", "") for target in ok} - {""}),
                       "ok": ok, "failed": failed}
    return status


def table(rows, opencpn):
    now = datetime.now(timezone.utc)
    lines = [f"Upstream status, {now:%Y-%m-%d %H:%M} UTC" + (f", checked against OpenCPN {opencpn}" if opencpn else ""),
             "", "| Plugin | Release | Needs OpenCPN | Released | Commits since | Release interval | "
             "Next milestone | Our build |", "|---|---|---|---|---|---|---|---|"]
    for row in rows:
        needs = row["needs_opencpn"] or "?"
        if row.get("opencpn_ok") is False:
            needs = f"**{needs}** ⚠"
        released = parse_date(row["released"])
        built = row["built"]
        ours = (" ".join(built["versions"]) + f" ({len(built['ok'])} targets)") if built["ok"] else "-"
        if built["failed"]:
            ours += f", {len(built['failed'])} failed"
        if row["source"].startswith("WARNING"):
            ours += " ⚠ " + row["source"].removeprefix("WARNING: ")
        milestone = row.get("next_milestone")
        lines.append("| " + " | ".join([
            row["plugin"],
            row["release"] or "-",
            needs,
            f"{released:%Y-%m-%d} ({days(now - released)} ago)" if released else "-",
            "-" if row["commits_since_release"] is None else str(row["commits_since_release"]),
            f"~{row['release_interval_days']} d" if row.get("release_interval_days") else "-",
            f"{milestone['title']} ({milestone['due']})" if milestone else "-",
            ours,
        ]) + " |")
    return "\n".join(lines)


def current_manifest():
    try:
        result = subprocess.run(["gh", "release", "download", "current", "-p", "manifest.json", "-O", "-"],
                                cwd=ROOT, capture_output=True, text=True, timeout=60)
        return json.loads(result.stdout) if result.returncode == 0 else {}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plugins", nargs="*")
    parser.add_argument("--opencpn", default=os.getenv("OPENCPN_VERSION", ""),
                        help="flag releases that need a newer OpenCPN than this")
    parser.add_argument("--manifest", type=Path, help="build state; default: the current release's")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    plugins = args.plugins or bt.plugins()
    manifest = json.loads(args.manifest.read_text()) if args.manifest else current_manifest()
    catalog.load()
    with ThreadPoolExecutor(12) as pool:
        rows = list(pool.map(lambda plugin: plugin_status(plugin, manifest, args.opencpn), plugins))
    print(json.dumps(rows, indent=2) if args.json else table(rows, args.opencpn))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

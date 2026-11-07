#!/usr/bin/env python3
"""Static analysis and vulnerability scans for a plugin checkout and its tarballs.

Source scans run in containers: cppcheck (static analysis), OSV-Scanner
(known vulnerabilities in submodules and bundled libraries) and Trivy
(vulnerabilities and committed secrets). The ELF hardening check reads the
shared libraries in the built tarballs with readelf. Findings never fail a
build. They are written to dist/analysis/<plugin>/ with a summary.json.
"""

import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import platform as host_platform
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_target", ROOT / "scripts" / "build-target.py")
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)

ANALYSIS_DOCKERFILE = ROOT / "docker" / "analysis" / "Dockerfile"
ANALYSIS_BASE = "ubuntu:26.04"
OSV_IMAGE = os.getenv("OSV_SCANNER_IMAGE", "ghcr.io/google/osv-scanner:v2.7.0")
TRIVY_IMAGE = os.getenv("TRIVY_IMAGE", "aquasec/trivy:0.76.2")
TIMEOUT = 45 * 60


def host_docker_platform():
    machine = host_platform.machine().lower()
    return "linux/arm64" if machine in {"aarch64", "arm64"} else "linux/amd64"


def container(image, source, output, *args):
    command = [*bt.DOCKER, "run", "--rm", "--env", "HOME=/tmp",
               *bt.mount(source, "/src", True), *bt.mount(output, "/out")]
    if bt.USER:
        command += ["--user", bt.USER]
    return command + [image, *args]


def run_to_file(command, path):
    with path.open("wb") as stream:
        return subprocess.run(command, stdout=stream, stderr=subprocess.PIPE,
                              timeout=TIMEOUT).returncode


def submodule_paths(source):
    result = subprocess.run(["git", "-C", str(source), "submodule", "status", "--recursive"],
                            capture_output=True, text=True)
    return [line.split()[1] for line in result.stdout.splitlines() if len(line.split()) > 1]


def cppcheck(source, output):
    status, image = bt.ensure_image("opencpn-analysis", ANALYSIS_DOCKERFILE, ANALYSIS_BASE,
                                    host_docker_platform(), output / "image.log")
    if status:
        return {"error": "analysis image build failed"}
    report = output / "cppcheck.xml"
    command = container(image, source, output, "cppcheck", "--enable=warning,performance,portability",
                        "--inline-suppr", "--suppress=missingIncludeSystem", "--xml", "--quiet",
                        f"-j{os.cpu_count() or 2}", "--output-file=/out/cppcheck.xml",
                        "-i/src/build", "/src")
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=(output / "cppcheck.log").open("wb"),
                   timeout=TIMEOUT)
    if not report.is_file():
        return {"error": "cppcheck produced no report"}
    vendored = tuple(f"/src/{path}/" for path in submodule_paths(source))
    counts = Counter()
    for error in ET.parse(report).getroot().iter("error"):
        location = error.find("location")
        if location is not None and location.get("file", "").startswith(vendored):
            counts["in_submodules"] += 1
        else:
            counts[error.get("severity", "other")] += 1
    return dict(counts)


def osv(source, output):
    report = output / "osv.json"
    status = run_to_file(container(OSV_IMAGE, source, output, "scan", "source", "-r",
                                   "--format", "json", "/src"), report)
    # 0: nothing found, 1: vulnerabilities found, 128: no packages to scan.
    if status == 128:
        return {"vulnerabilities": 0, "packages": 0}
    if status not in (0, 1):
        return {"error": f"osv-scanner exit status {status}"}
    results = json.loads(report.read_text() or "{}").get("results") or []
    packages = [package for result in results for package in result.get("packages") or []]
    return {"vulnerabilities": sum(len(package.get("vulnerabilities") or []) for package in packages),
            "packages": len(packages)}


def trivy(source, output):
    report = output / "trivy.json"
    status = run_to_file(container(TRIVY_IMAGE, source, output, "fs", "--quiet", "--scanners",
                                   "vuln,secret", "--cache-dir", "/tmp/trivy", "--format", "json",
                                   "/src"), report)
    if status:
        return {"error": f"trivy exit status {status}"}
    results = json.loads(report.read_text() or "{}").get("Results") or []
    return {"vulnerabilities": sum(len(result.get("Vulnerabilities") or []) for result in results),
            "secrets": sum(len(result.get("Secrets") or []) for result in results)}


def readelf(*args):
    return subprocess.run(["readelf", "-W", *args], capture_output=True, text=True).stdout


def hardening(tarballs):
    """Check RELRO, non-executable stack, stack protector and FORTIFY in each shared library."""
    findings = []
    for tarball in tarballs:
        with tempfile.TemporaryDirectory() as scratch, tarfile.open(tarball, "r:gz") as archive:
            members = [member for member in archive.getmembers()
                       if member.isfile() and ".so" in Path(member.name).name]
            for member in members:
                archive.extract(member, scratch, filter="data")
                library = str(Path(scratch, member.name))
                headers, dynamic, symbols = readelf("-l", library), readelf("-d", library), readelf("--dyn-syms", library)
                if "ELF" not in readelf("-h", library):
                    continue
                stack = [line for line in headers.splitlines() if "GNU_STACK" in line]
                findings.append({
                    "tarball": Path(tarball).name,
                    "library": member.name,
                    "relro": ("full" if "BIND_NOW" in dynamic or "FLAGS_1" in dynamic and "NOW" in dynamic
                              else "partial") if "GNU_RELRO" in headers else "none",
                    "nx": bool(stack) and "RWE" not in stack[0],
                    "stack_protector": "__stack_chk_fail" in symbols,
                    "fortify": "_chk@" in symbols or "_chk " in symbols,
                })
    return findings


def analyze(plugin, tarballs=(), source_scans=True):
    source = bt.ROOT / "repos" / plugin
    output = bt.ROOT / "dist" / "analysis" / plugin
    output.mkdir(parents=True, exist_ok=True)
    summary_path = output / "summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.is_file() else {}
    if source_scans:
        summary["commit"] = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"],
                                                    text=True).strip()
        for name, scan in (("cppcheck", cppcheck), ("osv", osv), ("trivy", trivy)):
            print(f"{plugin}: {name}", flush=True)
            try:
                summary[name] = scan(source, output)
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                summary[name] = {"error": str(error)}
    if tarballs:
        known = {item["library"] + "@" + item["tarball"]: item for item in summary.get("hardening", [])}
        for item in hardening(tarballs):
            known[item["library"] + "@" + item["tarball"]] = item
        summary["hardening"] = list(known.values())
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plugin")
    parser.add_argument("--no-source", action="store_true", help="skip the source scans")
    parser.add_argument("tarballs", nargs="*", type=Path, help="built tarballs for the ELF hardening check")
    args = parser.parse_args()
    if not (bt.ROOT / "repos" / args.plugin / ".git").exists():
        parser.exit(1, f"No checkout in repos/{args.plugin}\n")
    print(json.dumps(analyze(args.plugin, args.tarballs, not args.no_source), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

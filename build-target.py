#!/usr/bin/env python3
"""Choose a build environment and collect a plugin tarball and build logs."""

import argparse
import json
import os
from pathlib import Path
import platform as host_platform
import re
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET
import tempfile

ROOT = Path(__file__).resolve().parent
TARGETS = json.loads((ROOT / "targets.json").read_text(encoding="utf-8"))
NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\Z")


def run_logged(command, path, **kwargs):
    with path.open("wb") as log, subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs
    ) as process:
        for line in process.stdout:
            log.write(line)
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
        return process.wait()


def mount(path, destination, readonly=False):
    return ["--mount", f"type=bind,src={path},dst={destination}" + (",readonly" if readonly else "")]


def validate_packages(directory, target_tuple):
    packages = sorted(directory.glob("*.tar.gz"))
    if not packages:
        raise ValueError("No OpenCPN import packages found")
    failures = []
    for path in packages:
        try:
            with tarfile.open(path, "r:gz") as archive:
                entries = [member for member in archive.getmembers()
                           if member.isfile() and Path(member.name).name == "metadata.xml"]
                if len(entries) != 1 or entries[0].size > 64 * 1024:
                    raise ValueError("expected exactly one metadata.xml of at most 64 KiB")
                with archive.extractfile(entries[0]) as stream:
                    metadata = ET.parse(stream).getroot()
            actual = ";".join(metadata.findtext(key, "").strip() for key in
                              ("target", "target-version", "target-arch"))
            if not all(actual.split(";")) or target_tuple and actual != target_tuple:
                raise ValueError(f"metadata target {actual!r} does not match {target_tuple or 'the required fields'}")
            print(f"{path.name}: {actual}", flush=True)
        except (ValueError, tarfile.TarError, ET.ParseError) as error:
            path.rename(path.with_suffix(".rejected"))
            failures.append(f"{path.name}: {error}")
    if failures:
        raise ValueError("\n".join(failures))


def build(target, repo):
    source = ROOT / repo
    if not NAME.fullmatch(repo) or not (source / ".git").is_dir() or not (source / "build.sh").is_file():
        raise ValueError(f"Missing checkout or build.sh: {repo}")
    profile = TARGETS[target]
    if "base" not in profile and (sys.platform != profile["os"] or
                                  host_platform.machine().lower() != profile["arch"]):
        raise ValueError(f"{target} requires its native runner: {profile['runner']}")
    override = ROOT / "overrides" / repo / target
    recipe = override / "build.sh"
    helper = ROOT / "package-build.sh"
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix=f"{target}-{repo}.", dir=dist))
    print(f"Build output and logs: {destination}", flush=True)
    for filename, command in (
        ("source-commit.txt", ["rev-parse", "HEAD"]),
        ("source-url.txt", ["remote", "get-url", "origin"]),
    ):
        value = subprocess.check_output(["git", "-C", str(source), *command], text=True)
        (destination / filename).write_text(value, encoding="utf-8")
    (destination / "target.txt").write_text(f"{target}\n", encoding="utf-8")

    target_tuple = profile.get("tuple", "")
    if "base" not in profile:
        status = run_logged(["bash", helper.as_posix(), source.as_posix(), destination.as_posix(),
                           recipe.as_posix() if recipe.is_file() else ""], destination / "build.log")
        if not status:
            validate_packages(destination, target_tuple)
        return status

    dockerfile = override / "Dockerfile"
    if not dockerfile.is_file():
        dockerfile = ROOT / "Dockerfile"
    image = f"opencpn-plugin-builder:{target}" if dockerfile == ROOT / "Dockerfile" else (
        f"opencpn-plugin-builder:{target}-{repo.lower()}"
    )
    platform = profile["platform"]
    status = run_logged(
        ["docker", "build", "--platform", platform, "--build-arg", f"BASE_IMAGE={profile['base']}",
         "-f", str(dockerfile), "-t", image, str(ROOT)], destination / "image.log"
    )
    if status:
        return status

    command = ["docker", "run", "--rm", "--platform", platform,
               "--user", f"{os.getuid()}:{os.getgid()}",
               "--env", f"OPENCPN_TARGET_TUPLE={target_tuple}",
               "--env", f"OPENCPN_BUILD_JOBS={os.getenv('OPENCPN_BUILD_JOBS', '2')}",
               *mount(source, "/source", True), *mount(helper, "/package-build.sh", True),
               *mount(destination, "/output")]
    if recipe.is_file():
        command += mount(recipe, "/recipe.sh", True)
    command += [image, "bash", "/package-build.sh", "/source", "/output",
                "/recipe.sh" if recipe.is_file() else ""]
    status = run_logged(command, destination / "build.log")
    if not status:
        validate_packages(destination, target_tuple)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    show = commands.add_parser("show")
    show.add_argument("target", choices=TARGETS)
    compile_cmd = commands.add_parser("build")
    compile_cmd.add_argument("target", choices=TARGETS)
    compile_cmd.add_argument("repo")
    args = parser.parse_args()
    if args.command == "list":
        print("\n".join(TARGETS))
        return 0
    if args.command == "show":
        print(json.dumps(TARGETS[args.target], separators=(",", ":")))
        return 0
    try:
        return build(args.target, args.repo)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())

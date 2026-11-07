#!/usr/bin/env python3
"""Build one plugin for one target and collect its tarball and logs."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform as host_platform
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
TARGETS = json.loads((ROOT / "targets.json").read_text(encoding="utf-8"))
# Docker command, e.g. OPENCPN_DOCKER="sudo docker" where Docker needs root.
DOCKER = shlex.split(os.getenv("OPENCPN_DOCKER", "docker"))
# Run containers as the invoking user, also when this script itself runs under sudo.
USER = (f"{os.getenv('SUDO_UID', os.getuid())}:{os.getenv('SUDO_GID', os.getgid())}"
        if hasattr(os, "getuid") else "")
NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\Z")
# Docker platform architecture -> (uname -m values, binfmt_misc handler names)
ARCHES = {
    "amd64": ({"x86_64", "amd64"}, ("qemu-x86_64",)),
    "arm64": ({"aarch64", "arm64"}, ("qemu-aarch64",)),
    "arm": ({"armv7l", "armv8l"}, ("qemu-arm",)),
}


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


def plugins():
    return sorted(path.name for path in (ROOT / "plugins").iterdir()
                  if (path / "build.sh").is_file() and NAME.fullmatch(path.name))


def supports(plugin, target):
    """A plugin may restrict its targets with a plugins/<name>/targets file."""
    listing = ROOT / "plugins" / plugin / "targets"
    if not listing.is_file():
        return True
    wanted = {line.split("#")[0].strip() for line in listing.read_text(encoding="utf-8").splitlines()}
    return target in wanted


def runnable(target):
    """Return None if this host can build the target, otherwise the reason."""
    profile = TARGETS[target]
    machine = host_platform.machine().lower()
    if "base" not in profile:
        if sys.platform == profile["os"] and machine == profile["arch"]:
            return None
        return f"native build, needs {profile['runner']}"
    if shutil.which(DOCKER[0]) is None:
        return f"{DOCKER[0]} not found"
    arch = profile["platform"].split("/")[1]
    names, handlers = ARCHES[arch]
    if machine in names:
        return None
    if any(Path("/proc/sys/fs/binfmt_misc", handler).exists() for handler in handlers):
        return None
    return f"needs {arch} emulation ({shlex.join(DOCKER)} run --privileged --rm tonistiigi/binfmt --install {arch})"


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


# Files in a plugin directory that are build inputs, not part of its environment.
RECIPE_FILES = {"build.sh", "fetch.sh", "targets"}


def environment_hash(*parts, context=None):
    """Hash everything an image depends on, so it is rebuilt only when that changes."""
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode() + b"\0")
    if context:
        for path in sorted(context.rglob("*")):
            if path.is_file() and path.relative_to(context).parts[0] not in RECIPE_FILES:
                digest.update(path.relative_to(context).as_posix().encode() + b"\0")
                digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def build_key(target, plugin, commit):
    """Identify a build: source commit, recipe, shared scripts and environment.

    The same key means the same inputs, so a build with a known key is skipped in CI.
    """
    profile = TARGETS[target]
    digest = hashlib.sha256()
    digest.update(json.dumps([commit, target, profile], sort_keys=True).encode())
    if "base" in profile:
        dockerfile = ROOT / profile.get("dockerfile", "docker/base/Dockerfile")
        digest.update(environment_hash(profile["base"], profile["platform"],
                                       *image_args(profile.get("build_args")),
                                       context=dockerfile.parent).encode())
    inputs = [ROOT / "plugins" / plugin, SCRIPTS / "package-build.sh", SCRIPTS / "cmake-plugin.sh",
              SCRIPTS / "plugin-entry.sh"]
    for path in inputs:
        for file in sorted([path] if path.is_file() else path.rglob("*")):
            if file.is_file():
                digest.update(file.relative_to(ROOT).as_posix().encode() + b"\0" + file.read_bytes())
    return digest.hexdigest()[:16]


def image_args(build_args):
    """Extra docker build arguments of a target, e.g. the Android NDK version."""
    return [f"{key}={value}" for key, value in sorted((build_args or {}).items())]


def ensure_image(name, dockerfile, base, platform, log, rebuild=False, build_args=None):
    """Build an environment image unless one with the same inputs already exists."""
    extra = image_args(build_args)
    tag = f"{name}:{environment_hash(base, platform, *extra, context=dockerfile.parent)}"
    exists = subprocess.run([*DOCKER, "image", "inspect", tag], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL).returncode == 0
    if exists and not rebuild:
        print(f"Environment {tag} is up to date", flush=True)
        return 0, tag
    print(f"Building environment {tag}", flush=True)
    arguments = [value for arg in [f"BASE_IMAGE={base}", *extra] for value in ("--build-arg", arg)]
    status = run_logged([*DOCKER, "build", "--platform", platform, *arguments,
                         "--label", "opencpn-plugin-builds=1", "-f", str(dockerfile), "-t", tag,
                         str(dockerfile.parent)], log)
    return status, tag


def environment(target, plugin=None, log_dir=None, rebuild=False):
    """Return the environment image for a target, plus the plugin's own layer if it has one."""
    profile = TARGETS[target]
    if log_dir is None:
        log_dir = ROOT / "dist" / "images" / target
        log_dir.mkdir(parents=True, exist_ok=True)
    dockerfile = ROOT / profile.get("dockerfile", "docker/base/Dockerfile")
    status, image = ensure_image(f"opencpn-env-{target}", dockerfile, profile["base"],
                                 profile["platform"], log_dir / "image.log", rebuild,
                                 profile.get("build_args"))
    plugin_dockerfile = ROOT / "plugins" / plugin / "Dockerfile" if plugin else None
    if status or not plugin_dockerfile or not plugin_dockerfile.is_file():
        return status, image
    return ensure_image(f"opencpn-env-{target}-{plugin.lower()}", plugin_dockerfile, image,
                        profile["platform"], log_dir / "plugin-image.log", rebuild)


def build(target, plugin):
    recipe_dir = ROOT / "plugins" / plugin
    source = ROOT / "repos" / plugin
    if not NAME.fullmatch(plugin) or not (recipe_dir / "build.sh").is_file():
        raise ValueError(f"No plugins/{plugin}/build.sh")
    if not (source / ".git").exists():
        raise ValueError(f"No checkout in repos/{plugin}. Run ./fetch.sh {plugin}")
    reason = runnable(target)
    if reason:
        raise ValueError(f"{target} cannot be built on this host: {reason}")
    profile = TARGETS[target]
    destination = ROOT / "dist" / target / plugin
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    print(f"Build output and logs: {destination.relative_to(ROOT)}", flush=True)
    for filename, command in (
        ("source-commit.txt", ["rev-parse", "HEAD"]),
        ("source-url.txt", ["remote", "get-url", "origin"]),
    ):
        value = subprocess.check_output(["git", "-C", str(source), *command], text=True)
        (destination / filename).write_text(value, encoding="utf-8")
    target_tuple = profile.get("tuple", "")
    env = {
        "OPENCPN_TARGET": target,
        "OPENCPN_TARGET_TUPLE": target_tuple,
        "OPENCPN_BUILD_JOBS": os.getenv("OPENCPN_BUILD_JOBS", str(os.cpu_count() or 2)),
    }

    if "base" not in profile:
        status = run_logged(["bash", str(SCRIPTS / "package-build.sh"), str(source),
                             str(recipe_dir / "build.sh"), str(destination)],
                            destination / "build.log", env=dict(os.environ, **env))
    else:
        status, image = environment(target, plugin, destination)
        if status:
            return status
        # The whole repository is mounted read-only. Only the output directory is writable.
        work = PurePosixPath("/work")
        output = work / destination.relative_to(ROOT).as_posix()
        command = [*DOCKER, "run", "--rm", "--platform", profile["platform"],
                   "--user", USER]
        for key, value in env.items():
            command += ["--env", f"{key}={value}"]
        command += [*mount(ROOT, work, True), *mount(destination, output), image,
                    "bash", str(work / "scripts/package-build.sh"), str(work / "repos" / plugin),
                    str(work / "plugins" / plugin / "build.sh"), str(output)]
        status = run_logged(command, destination / "build.log")
    if not status:
        validate_packages(destination, target_tuple)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("targets", help="list targets")
    listing.add_argument("--runnable", action="store_true", help="only targets this host can build")
    listing.add_argument("--why", action="store_true", help="print the reason for skipped targets")
    listing.add_argument("--containers", action="store_true", help="only container targets")
    plugin_list = commands.add_parser("plugins", help="list plugins")
    plugin_list.add_argument("--target", help="only plugins that support this target")
    show = commands.add_parser("show", help="print a target profile as JSON")
    show.add_argument("target", choices=TARGETS)
    matrix = commands.add_parser("matrix", help="GitHub Actions matrix for a target")
    matrix.add_argument("target", choices=TARGETS)
    matrix.add_argument("--match", default="", help="plugin directory name filter")
    images = commands.add_parser("image", help="build a target's environment image if it changed")
    images.add_argument("target", choices=TARGETS)
    images.add_argument("plugin", nargs="?", help="also build this plugin's own environment layer")
    images.add_argument("--rebuild", action="store_true", help="build even if the image exists")
    compile_cmd = commands.add_parser("build")
    compile_cmd.add_argument("target", choices=TARGETS)
    compile_cmd.add_argument("plugin")
    args = parser.parse_args()

    if args.command == "targets":
        for target in TARGETS:
            if args.containers and "base" not in TARGETS[target]:
                continue
            reason = runnable(target) if args.runnable or args.why else None
            if reason and args.why:
                print(f"{target}: {reason}", file=sys.stderr)
            if not reason or not args.runnable:
                print(target)
        return 0
    if args.command == "plugins":
        print("\n".join(name for name in plugins() if not args.target or supports(name, args.target)))
        return 0
    if args.command == "show":
        print(json.dumps(TARGETS[args.target], separators=(",", ":")))
        return 0
    if args.command == "matrix":
        names = [name for name in plugins() if supports(name, args.target)
                 and args.match.casefold() in name.casefold()]
        print(json.dumps({"include": [{"plugin": name} for name in names]}))
        return 0
    try:
        if args.command == "image":
            if "base" not in TARGETS[args.target]:
                raise ValueError(f"{args.target} is a native build without a container")
            reason = runnable(args.target)
            if reason:
                raise ValueError(f"{args.target} cannot be built on this host: {reason}")
            return environment(args.target, args.plugin, rebuild=args.rebuild)[0]
        return build(args.target, args.plugin)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())

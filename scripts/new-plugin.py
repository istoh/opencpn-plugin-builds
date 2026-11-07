#!/usr/bin/env python3
"""Create plugins/<name>/fetch.sh and build.sh from the OpenCPN master catalog."""

import argparse
from collections import defaultdict
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
from urllib.request import urlopen
import xml.etree.ElementTree as ET

MASTER = "https://raw.githubusercontent.com/OpenCPN/plugins/master/ocpn-plugins.xml"
MAX_CATALOG = 16 * 1024 * 1024
FORGES = {"github.com", "gitlab.com", "codeberg.org", "bitbucket.org"}
ROOT = Path(__file__).resolve().parent.parent
# Catalog entries without a source element, matched by release tags upstream.
MISSING_SOURCES = {
    "Logbook": "https://github.com/rgleason/LogbookKonni_pi.git",
    "VDR": "https://github.com/rgleason/vdr_pi.git",
}
COMPONENT = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\Z")

FETCH_SCRIPT = """#!/usr/bin/env bash
# Source of the {names} plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url={url}
ref=
exec bash "$(dirname -- "${{BASH_SOURCE[0]}}")/../../scripts/git-fetch.sh" {directory} "$url" "$ref"
"""

BUILD_SCRIPT = """#!/usr/bin/env bash
# On the host: plugins/{directory}/build.sh [-t TARGET]... builds this plugin in
# the target containers (see ./build.sh --help).
# In the container, the recipe below runs in a scratch copy of repos/{directory}.
# Environment: OPENCPN_TARGET, OPENCPN_TARGET_TUPLE, OPENCPN_BUILD_JOBS,
# OPENCPN_BUILD_DIR, OPENCPN_PLUGIN_DIR (this directory), OPENCPN_SCRIPTS.
# Leave the import tarball (*.tar.gz with metadata.xml) anywhere in the tree.
set -euo pipefail
source "$(dirname -- "${{BASH_SOURCE[0]}}")/../../scripts/plugin-entry.sh"

cmake_plugin
"""


def repository(source):
    source = re.sub(r"\A(https?://)+(?=https?://)", "", source)  # "https://https://..."
    url = urlsplit(source)
    host = url.hostname
    if host not in FORGES or url.scheme not in {"http", "https", "git"}:
        return None
    parts = url.path.strip("/").split("/")
    if host == "gitlab.com":
        if "-" in parts:
            parts = parts[:parts.index("-")]
    else:
        parts = parts[:2]
    if len(parts) < 2:
        return None
    parts[-1] = parts[-1].removesuffix(".git")
    if not all(COMPONENT.fullmatch(part) for part in parts):
        return None
    return f"https://{host}/{'/'.join(parts)}.git"


def read_catalog(path):
    stream = path.open("rb") if path else urlopen(MASTER, timeout=30)
    with stream:
        data = stream.read(MAX_CATALOG + 1)
    if len(data) > MAX_CATALOG:
        raise ValueError("catalog exceeds 16 MiB")
    root = ET.fromstring(data)
    if root.tag != "plugins":
        raise ValueError("expected an OpenCPN plugins catalog")
    return root.findall("plugin")


def scaffold(directory, url, names):
    destination = ROOT / "plugins" / directory
    if destination.exists():
        return "plugins/{} already exists, kept".format(directory)
    destination.mkdir(parents=True)
    for filename, template in (("fetch.sh", FETCH_SCRIPT), ("build.sh", BUILD_SCRIPT)):
        script = destination / filename
        script.write_text(template.format(directory=directory, url=url,
                                          names=", ".join(sorted(names))), encoding="utf-8")
        script.chmod(0o755)
    return "plugins/{} created".format(directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, help="read local XML instead of the master catalog")
    parser.add_argument("--match", action="append", default=[],
                        help="limit to plugin names containing this text (repeatable)")
    parser.add_argument("--list", action="store_true", help="print what would be created")
    parser.add_argument("--repo", help="select an exact plugin directory name")
    args = parser.parse_args()

    repos = defaultdict(set)
    canonical_urls = {}
    missing = set()
    known = set()
    try:
        for item in read_catalog(args.catalog):
            name = item.findtext("name", "").strip()
            if not name or args.match and not any(query.casefold() in name.casefold()
                                                  for query in args.match):
                continue
            url = repository(item.findtext("source", "").strip()) or MISSING_SOURCES.get(name)
            if url:
                repos[url.casefold()].add(name)
                canonical_urls.setdefault(url.casefold(), url)
                known.add(name)
            else:
                missing.add(name)
    except (OSError, ValueError, ET.ParseError) as error:
        parser.exit(1, f"{error}\n")

    for name in sorted(missing - known):
        print(f"No supported public Git source in catalog: {name}", file=sys.stderr)
    if not repos:
        parser.exit(1, "No matching public Git repositories.\n")

    short_names = defaultdict(int)
    for url in repos:
        short_names[Path(urlsplit(url).path).stem] += 1
    plan = []
    for key, names in sorted(repos.items()):
        url = canonical_urls[key]
        path = Path(urlsplit(url).path)
        directory = path.stem
        if short_names[directory.casefold()] > 1:
            directory = urlsplit(url).hostname + "--" + "--".join(path.parts[1:-1]) + "--" + directory
        if args.repo is None or directory == args.repo:
            plan.append((directory, url, names))
    if not plan:
        parser.exit(1, "No plugin directory matches --repo.\n")

    for directory, url, names in plan:
        print(f"{directory}  {url}  ({', '.join(sorted(names))})", flush=True)
        if args.list:
            continue
        print(f"  {scaffold(directory, url, names)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

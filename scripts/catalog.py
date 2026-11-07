#!/usr/bin/env python3
"""The OpenCPN master plugin catalog: released versions and their source tags.

  catalog.py release-ref URL NAME...   print "<ref> <description>" for the newest release
  catalog.py entries NAME...           print the catalog entries as JSON
"""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

MASTER = "https://raw.githubusercontent.com/OpenCPN/plugins/master/ocpn-plugins.xml"
MAX_CATALOG = 16 * 1024 * 1024
CACHE = Path(os.getenv("OPENCPN_CATALOG_CACHE")
             or Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache")) / "opencpn-plugin-builds"
             / "ocpn-plugins.xml")
MAX_AGE = 3600
_entries = None
# Plugin API version -> first OpenCPN release that provides it, from the
# opencpn_plugin_1xx classes in each release's ocpn_plugin.h.
OPENCPN_FOR_API = {"1.16": "5.0", "1.17": "5.2", "1.18": "5.8", "1.19": "5.12", "1.20": "5.12",
                   "1.21": "5.14", "1.22": "5.14"}


def min_opencpn(api):
    """The oldest OpenCPN that loads a plugin built for this API version, or None if unknown."""
    if api in OPENCPN_FOR_API:
        return OPENCPN_FOR_API[api]
    newer = [version for known, version in OPENCPN_FOR_API.items() if version_key(known) >= version_key(api)]
    return min(newer, key=version_key) if newer else None


def load():
    """Catalog entries as dicts, cached for an hour so parallel lookups share one download."""
    global _entries
    if _entries is not None:
        return _entries
    if not CACHE.is_file() or time.time() - CACHE.stat().st_mtime > MAX_AGE:
        with urlopen(MASTER, timeout=60) as stream:
            data = stream.read(MAX_CATALOG + 1)
        if len(data) > MAX_CATALOG:
            raise ValueError("catalog exceeds 16 MiB")
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=CACHE.parent, delete=False) as output:
            output.write(data)
        os.replace(output.name, CACHE)
    root = ET.fromstring(CACHE.read_bytes())
    _entries = [{child.tag: (child.text or "").strip() for child in plugin} for plugin in root.findall("plugin")]
    return _entries


def entries(names):
    wanted = {name.casefold() for name in names}
    return [entry for entry in load() if entry.get("name", "").casefold() in wanted]


def version_key(version):
    """Sort key: numeric parts first, so 1.10 > 1.9; a pre-release sorts before its release."""
    core, _, _ = version.lstrip("vV").partition("+")
    numbers = [int(part) for part in re.findall(r"\d+", re.split(r"[-~]", core)[0])]
    while numbers and numbers[-1] == 0:
        numbers.pop()
    return numbers, "-" not in core and "~" not in core, core


def newest_version(names):
    versions = {entry.get("version", "") for entry in entries(names)} - {""}
    return max(versions, key=version_key) if versions else None


def normalize(version):
    """Comparable form of a version or tag: no v prefix, no build metadata, no trailing .0."""
    core = version.strip().lstrip("vV").partition("+")[0].casefold()
    while core.endswith(".0"):
        core = core[:-2]
    return core


def remote_tags(url):
    output = subprocess.run(["git", "ls-remote", "--tags", "--", url], capture_output=True,
                            text=True, timeout=120, env=dict(os.environ, GIT_TERMINAL_PROMPT="0")).stdout
    tags = {}
    for line in output.splitlines():
        commit, ref = line.split("\t")
        name = ref.removeprefix("refs/tags/")
        if name.endswith("^{}"):
            tags[name[:-3]] = commit  # the peeled commit of an annotated tag wins
        else:
            tags.setdefault(name, commit)
    return tags


def github_token():
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        try:
            token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True,
                                   timeout=10).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            token = ""
    return token


def github_api(url, path):
    """GET a GitHub API path for the repository at url, or None if it is not on GitHub."""
    match = re.match(r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
    if not match:
        return None
    request = Request(f"https://api.github.com/repos/{match[1]}/{match[2]}/{path}",
                      headers={"Accept": "application/vnd.github+json"})
    token = github_token()
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except (OSError, ValueError):
        return None


def full_commit(url, commit):
    if len(commit) == 40:
        return commit
    found = github_api(url, f"commits/{commit}")
    return found.get("sha") if isinstance(found, dict) else None


def release_ref(url, names):
    """The git ref of the newest catalog release: (ref, description), or (None, reason)."""
    version = newest_version(names)
    if not version:
        return None, "no catalog release"
    wanted = normalize(version)
    tags = remote_tags(url)
    # Tags are often "v1.2", sometimes "<name>-1.2" or "release-1.2".
    matches = [tag for tag in tags if normalize(tag) == wanted
               or normalize(re.sub(r"^[A-Za-z_]+[-_]", "", tag)) == wanted]
    if matches:
        tag = min(matches, key=len)
        return tag, f"release {version} (tag {tag})"
    build = re.search(r"\+.*?\b([0-9a-f]{7,40})$", version)
    if build:
        commit = full_commit(url, build.group(1))
        if commit:
            return commit, f"release {version} (commit {build.group(1)})"
    return None, f"no tag for release {version}"


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "entries":
        print(json.dumps(entries(sys.argv[2:]), indent=2))
        return 0
    if len(sys.argv) >= 4 and sys.argv[1] == "release-ref":
        ref, description = release_ref(sys.argv[2], sys.argv[3:])
        if not ref:
            print("-", description)
            return 1
        print(ref, description)
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

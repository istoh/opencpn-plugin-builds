#!/usr/bin/env python3
"""Compare a built plugin tarball with the official catalog package for the same target.

The packages are not expected to be byte-identical (different compilers and build
dates). The comparison shows whether they are the same plugin: version, plugin API,
file list, and for each shared library its NEEDED libraries and exported symbols.

  compare.py PLUGIN TARGET [TARBALL]

Writes dist/<target>/<plugin>/compare.json and prints a summary.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import tempfile
from urllib.request import urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bt = load("build-target")
catalog = load("catalog")
DOWNLOADS = catalog.CACHE.parent / "packages"
MAX_PACKAGE = 256 * 1024 * 1024


def catalog_names(plugin):
    text = (ROOT / "plugins" / plugin / "fetch.sh").read_text(encoding="utf-8")
    match = re.search(r'OPENCPN_CATALOG_NAMES="([^"]*)"', text)
    return [name for name in (match.group(1).split(";") if match else []) if name]


def official_entry(names, tuple_):
    """The catalog package for this target: exact target, else the nearest version of it."""
    target, version, arch = tuple_.split(";")
    candidates = [entry for entry in catalog.entries(names) if entry.get("target-arch") == arch]
    newest = catalog.newest_version(names)
    candidates = [entry for entry in candidates if entry.get("version") == newest] or candidates
    exact = [entry for entry in candidates
             if entry.get("target") == target and entry.get("target-version") == version]
    if exact:
        return exact[0], "exact"
    # Debian, Ubuntu and Raspberry Pi OS packages are built the same way and are
    # the closest substitute for each other; prefer the same distribution, then wx 3.2.
    family = target.split("-")[0]
    debian_like = {"debian", "ubuntu", "raspbian"}
    related = debian_like if family in debian_like else {family}
    near = [entry for entry in candidates if entry.get("target", "").split("-")[0] in related]
    if near:
        return max(near, key=lambda entry: (entry.get("target", "").startswith(family),
                                            catalog.version_key(entry.get("target-version", "")))), "nearest"
    return None, "none"


def download(entry):
    url = entry.get("tarball-url", "")
    name = PurePosixPath(url.split("?")[0]).name
    if not url.startswith("https://") or not name.endswith(".tar.gz"):
        raise ValueError(f"unexpected tarball URL {url!r}")
    path = DOWNLOADS / name
    checksum = entry.get("tarball-checksum", "").lower()
    if not path.is_file():
        DOWNLOADS.mkdir(parents=True, exist_ok=True)
        with urlopen(url, timeout=120) as response:
            data = response.read(MAX_PACKAGE + 1)
        if len(data) > MAX_PACKAGE:
            raise ValueError("official package exceeds 256 MiB")
        if checksum and hashlib.sha256(data).hexdigest() != checksum:
            raise ValueError("official package SHA-256 does not match the catalog")
        path.write_bytes(data)
    return path


def readelf(*args):
    return subprocess.run(["readelf", "-W", *args], capture_output=True, text=True).stdout


# Demangled prefixes of symbols that the compiler emits from library headers
# (C++ standard library, wxWidgets inlines); they vary with the toolchain.
TOOLCHAIN_SYMBOLS = re.compile(r"^(?:(?:typeinfo|typeinfo name|vtable|VTT|guard variable|construction vtable) for )?"
                               r"(?:\S+ )?(?:std::|__gnu_cxx::|__cxxabiv1::|wx[A-Z]\w*(?:<[^>]*>)?::)")
ENTRY_POINTS = {"create_pi", "destroy_pi"}


def demangle(names):
    names = sorted(names)
    if not names:
        return {}
    result = subprocess.run(["c++filt"], input="\n".join(names), capture_output=True, text=True)
    lines = result.stdout.splitlines()
    return dict(zip(names, lines)) if len(lines) == len(names) else {name: name for name in names}


def library_facts(path):
    needed = set(re.findall(r"\(NEEDED\)\s+Shared library: \[([^\]]+)\]", readelf("-d", path)))
    symbols = set()
    for line in readelf("--dyn-syms", path).splitlines():
        fields = line.split()
        # Num: Value Size Type Bind Vis Ndx Name
        if len(fields) >= 8 and fields[3] in {"FUNC", "OBJECT"} and fields[4] in {"GLOBAL", "WEAK"} \
                and fields[6] != "UND":
            symbols.add(fields[7].split("@")[0])
    plugin_symbols = {name for name, readable in demangle(symbols).items()
                      if not TOOLCHAIN_SYMBOLS.match(readable)}
    return {"needed": needed, "symbols": plugin_symbols, "entry_points": ENTRY_POINTS & symbols,
            "size": Path(path).stat().st_size}


def unpack(tarball, directory):
    """Extract a package; return its metadata and files keyed by path below the top directory."""
    with tarfile.open(tarball, "r:gz") as archive:
        archive.extractall(directory, filter="data")
    files = {}
    metadata = {}
    for path in Path(directory).rglob("*"):
        if not path.is_file():
            continue
        parts = path.relative_to(directory).parts
        key = "/".join(parts[1:] if len(parts) > 1 else parts)
        if path.name == "metadata.xml":
            root = ET.parse(path).getroot()
            metadata = {child.tag: (child.text or "").strip() for child in root}
            continue
        files[key] = path
    return metadata, files


def compare(ours, official):
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        our_meta, our_files = unpack(ours, a)
        their_meta, their_files = unpack(official, b)
        libraries = {}
        for key in sorted(set(our_files) & set(their_files)):
            if ".so" not in PurePosixPath(key).name and not key.endswith((".dll", ".dylib")):
                continue
            mine, theirs = library_facts(our_files[key]), library_facts(their_files[key])
            libraries[key] = {
                "needed_added": sorted(mine["needed"] - theirs["needed"]),
                "needed_removed": sorted(theirs["needed"] - mine["needed"]),
                "symbols_added": len(mine["symbols"] - theirs["symbols"]),
                "symbols_removed": len(theirs["symbols"] - mine["symbols"]),
                "size_ratio": round(mine["size"] / theirs["size"], 2) if theirs["size"] else None,
                "missing_entry_points": sorted(theirs["entry_points"] - mine["entry_points"]),
            }
    result = {
        "version": [our_meta.get("version", ""), their_meta.get("version", "")],
        "api": [our_meta.get("api-version", ""), their_meta.get("api-version", "")],
        "files_added": sorted(set(our_files) - set(their_files)),
        "files_removed": sorted(set(their_files) - set(our_files)),
        "libraries": libraries,
    }
    same_libraries = all(not (item["needed_added"] or item["needed_removed"] or item["symbols_added"]
                              or item["symbols_removed"] or item["missing_entry_points"])
                         for item in libraries.values())
    result["same"] = (result["version"][0] == result["version"][1] and not result["files_added"]
                      and not result["files_removed"] and bool(libraries) and same_libraries)
    return result


def summary_line(result):
    if "error" in result:
        return f"not compared: {result['error']}"
    if result["same"]:
        return f"same as official {result['version'][1]} ({result['official']}, {result['match']})"
    parts = []
    if result["version"][0] != result["version"][1]:
        parts.append(f"version {result['version'][0]} vs {result['version'][1]}")
    if result["files_added"] or result["files_removed"]:
        parts.append(f"files +{len(result['files_added'])}/-{len(result['files_removed'])}")
    for key, item in result["libraries"].items():
        changes = []
        if item["missing_entry_points"]:
            changes.append("MISSING " + " ".join(item["missing_entry_points"]))
        if item["symbols_added"] or item["symbols_removed"]:
            changes.append(f"symbols +{item['symbols_added']}/-{item['symbols_removed']}")
        if item["needed_added"] or item["needed_removed"]:
            changes.append("NEEDED " + " ".join([f"+{n}" for n in item["needed_added"]]
                                                 + [f"-{n}" for n in item["needed_removed"]]))
        if changes:
            parts.append(f"{PurePosixPath(key).name}: {', '.join(changes)}")
    if not result["libraries"]:
        parts.append("no common shared library")
    return f"differs from official {result['official']} ({result['match']}): " + "; ".join(parts)


def run(plugin, target, tarball=None):
    names = catalog_names(plugin)
    tuple_ = bt.TARGETS[target].get("tuple", "")
    output = ROOT / "dist" / target / plugin
    if tarball is None:
        tarballs = sorted(output.glob("*.tar.gz"))
        tarball = tarballs[0] if tarballs else None
    try:
        if not tarball:
            raise ValueError("no built tarball")
        if not names or not tuple_:
            raise ValueError("no catalog name or target tuple")
        entry, match = official_entry(names, tuple_)
        if not entry:
            raise ValueError(f"no official package for {tuple_.replace(';', ' ')}")
        result = compare(tarball, download(entry))
        result.update(official=f"{entry.get('target')} {entry.get('target-version')}", match=match)
    except (OSError, ValueError, tarfile.TarError, ET.ParseError) as error:
        result = {"error": str(error), "same": False}
    result["summary"] = summary_line(result)
    if output.is_dir():
        (output / "compare.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plugin")
    parser.add_argument("target", choices=bt.TARGETS)
    parser.add_argument("tarball", nargs="?", type=Path)
    args = parser.parse_args()
    result = run(args.plugin, args.target, args.tarball)
    print(result["summary"])
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())

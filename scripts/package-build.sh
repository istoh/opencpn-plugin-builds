#!/usr/bin/env bash
# Run a plugin recipe in a scratch copy of its source and collect the
# OpenCPN import tarballs it produces.
# Usage: package-build.sh SOURCE RECIPE OUTPUT
# Used inside the build containers and directly on native runners.
set -euo pipefail
source_dir=$1
recipe=$(cd -- "$(dirname -- "$2")" && pwd)/$(basename -- "$2")
output=$(cd -- "$3" && pwd)
export OPENCPN_SCRIPTS=${OPENCPN_SCRIPTS:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)}
export OPENCPN_PLUGIN_DIR=${OPENCPN_PLUGIN_DIR:-$(dirname -- "$recipe")}
work=$(mktemp -d "${TMPDIR:-/tmp}/opencpn-plugin.XXXXXX")
trap 'rm -rf -- "$work"' EXIT
cp -a "$source_dir/." "$work/"
cd "$work"
export OPENCPN_BUILD_DIR=$(mktemp -d "$work/build-opencpn.XXXXXX")
marker=$(mktemp "$work/.build-start.XXXXXX")
bash "$recipe"

count=0
while IFS= read -r -d "" package; do
    if tar -tzf "$package" | grep -E '(^|/)metadata[.]xml$' >/dev/null; then
        cp -- "$package" "$output/"
        count=$((count + 1))
    fi
done < <(find . -name .git -prune -o -type f -name "*.tar.gz" -newer "$marker" -print0)
if (( count == 0 )); then
    printf 'Build produced no OpenCPN import tarball.\n' >&2
    exit 1
fi

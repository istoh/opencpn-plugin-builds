#!/usr/bin/env bash
set -euo pipefail
source_dir=$1
output=$2
recipe=${3:-}
work=$(mktemp -d "${TMPDIR:-/tmp}/opencpn-plugin.XXXXXX")
trap 'rm -rf -- "$work"' EXIT
cp -a "$source_dir/." "$work/"
cd "$work"
export OPENCPN_BUILD_DIR=build-container
if [[ -e "$OPENCPN_BUILD_DIR" ]]; then
    export OPENCPN_BUILD_DIR=$(mktemp -d "$work/build-container.XXXXXX")
fi
marker=$(mktemp "$work/.build-start.XXXXXX")
if [[ -n "$recipe" ]]; then
    bash "$recipe"
elif [[ -n ${OPENCPN_TARGET_TUPLE:-} ]]; then
    bash ./build.sh "-DOCPN_TARGET_TUPLE=${OPENCPN_TARGET_TUPLE}"
else
    bash ./build.sh
fi
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

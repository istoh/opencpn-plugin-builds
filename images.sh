#!/usr/bin/env bash
# Build the container build environments. An image is rebuilt only when its
# Dockerfile, base image or other files in its directory change.
# Usage: ./images.sh [--rebuild] [-t TARGET]... [PLUGIN...]
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
runner=(python3 "$root/scripts/build-target.py")
targets=()
plugins=()
rebuild=()
while (( $# )); do
    case $1 in
        -t|--target) targets+=("${2:?--target needs a name}"); shift ;;
        --rebuild) rebuild=(--rebuild) ;;
        -h|--help) sed -n '2,4s/^# \{0,1\}//p' "$0"; exit ;;
        *) plugins+=("$1") ;;
    esac
    shift
done
if (( ${#targets[@]} == 0 )); then
    mapfile -t targets < <("${runner[@]}" targets --runnable --containers --why)
fi
for target in "${targets[@]}"; do
    "${runner[@]}" image "${rebuild[@]}" "$target"
    for plugin in "${plugins[@]}"; do
        "${runner[@]}" image "${rebuild[@]}" "$target" "$plugin"
    done
done

#!/usr/bin/env bash
# Run plugins/<name>/fetch.sh for the named plugins, or for all of them.
# Usage: ./fetch.sh [--update] [PLUGIN...]
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ ${1:-} == --update ]]; then
    export OPENCPN_FETCH_UPDATE=1
    shift
fi
if (( $# )); then
    names=("$@")
else
    mapfile -t names < <(python3 "$root/scripts/build-target.py" plugins)
fi

failed=()
for name in "${names[@]}"; do
    if [[ ! -f $root/plugins/$name/fetch.sh ]]; then
        printf 'No plugins/%s/fetch.sh\n' "$name" >&2
        failed+=("$name")
    elif ! bash "$root/plugins/$name/fetch.sh"; then
        failed+=("$name")
    fi
done
if (( ${#failed[@]} )); then
    printf 'Fetch failed: %s\n' "${failed[*]}" >&2
    exit 1
fi

#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if (( $# )); then
    repos=()
    for name in "$@"; do
        if [[ $name == */* || $name == . || $name == .. ]]; then
            printf 'Expected a repository directory name: %s\n' "$name" >&2
            exit 2
        fi
        repos+=("$root/$name")
    done
else
    shopt -s nullglob
    repos=("$root"/*/)
fi

ok=0
failed=()
for repo in "${repos[@]}"; do
    repo=${repo%/}
    name=${repo##*/}
    if [[ ! -e "$repo/.git" || ! -f "$repo/build.sh" ]]; then
        if (( $# )) || [[ -e "$repo/.git" ]]; then
            printf 'Missing checkout or build.sh: %s\n' "$name" >&2
            failed+=("$name")
        fi
        continue
    fi
    printf '\n=== %s ===\n' "$name"
    if (cd -- "$repo" && bash ./build.sh); then
        ok=$((ok + 1))
    else
        failed+=("$name")
    fi
done

if (( ok == 0 && ${#failed[@]} == 0 )); then
    printf 'No repositories found. Run ./fetch.sh first.\n' >&2
    exit 1
fi
printf '\nBuilds succeeded: %d. Failed: %d.\n' "$ok" "${#failed[@]}"
if (( ${#failed[@]} )); then
    printf '  %s\n' "${failed[@]}"
    exit 1
fi

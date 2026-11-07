#!/usr/bin/env bash
# Clone or update a plugin repository under repos/.
# Usage: git-fetch.sh NAME URL [REF]
# REF is a branch, tag or commit. Without REF the default branch is used.
# An existing checkout is only moved when OPENCPN_FETCH_UPDATE=1 or REF changes.
# OPENCPN_FETCH_RESOLVE=1 only prints the commit REF points to upstream.
# OPENCPN_FETCH_COMMIT=<sha> checks out that commit instead of REF.
set -euo pipefail
name=$1
url=$2
ref=${3:-}
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
dest=$root/repos/$name
export GIT_TERMINAL_PROMPT=0

if [[ ${OPENCPN_FETCH_RESOLVE:-0} == 1 ]]; then
    if [[ $ref =~ ^[0-9a-f]{40}$ ]]; then
        echo "$ref"
        exit 0
    fi
    pattern=${ref:-HEAD}
    refs=$(git ls-remote -- "$url" "$pattern" "$pattern^{}")
    # A peeled annotated tag (^{}) names the commit; otherwise take the first match.
    commit=$(awk '$2 ~ /\^\{\}$/ {print $1; exit}' <<< "$refs")
    commit=${commit:-$(awk 'NR == 1 {print $1}' <<< "$refs")}
    if [[ -z $commit ]]; then
        printf '%s: %s not found in %s\n' "$name" "$pattern" "$url" >&2
        exit 1
    fi
    echo "$commit"
    exit 0
fi
ref=${OPENCPN_FETCH_COMMIT:-$ref}

if [[ ! -e $dest ]]; then
    mkdir -p -- "$root/repos"
    git clone --recurse-submodules -- "$url" "$dest"
    if [[ -n $ref ]]; then
        git -C "$dest" checkout --quiet --detach "$ref"
        git -C "$dest" submodule update --init --recursive
    fi
    printf '%s: cloned %s\n' "$name" "$(git -C "$dest" rev-parse --short HEAD)"
    exit 0
fi

if [[ ! -e $dest/.git ]]; then
    printf '%s: %s exists and is not a Git checkout\n' "$name" "$dest" >&2
    exit 1
fi
origin=$(git -C "$dest" remote get-url origin)
if [[ ${origin%.git} != "${url%.git}" ]]; then
    printf '%s: checkout origin %s does not match %s\n' "$name" "$origin" "$url" >&2
    exit 1
fi

if [[ -n $ref ]]; then
    current=$(git -C "$dest" rev-parse HEAD)
    if ! wanted=$(git -C "$dest" rev-parse --verify --quiet "$ref^{commit}") \
            || [[ ${OPENCPN_FETCH_UPDATE:-0} == 1 ]]; then
        git -C "$dest" fetch --tags --quiet origin
        wanted=$(git -C "$dest" rev-parse --verify "origin/$ref^{commit}" 2>/dev/null \
            || git -C "$dest" rev-parse --verify "$ref^{commit}")
    fi
    if [[ $current != "$wanted" ]]; then
        git -C "$dest" checkout --quiet --detach "$wanted"
        git -C "$dest" submodule update --init --recursive
    fi
elif [[ ${OPENCPN_FETCH_UPDATE:-0} == 1 ]]; then
    git -C "$dest" pull --ff-only --quiet
    git -C "$dest" submodule update --init --recursive
fi
printf '%s: at %s\n' "$name" "$(git -C "$dest" rev-parse --short HEAD)"

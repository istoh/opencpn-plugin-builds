#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if (( $# != 1 )) || [[ ! $1 =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]*$ ]]; then
    printf 'Usage: %s CHECKOUT_DIRECTORY\n' "$0" >&2
    exit 2
fi

repo=$1
source_dir="$root/$repo"
if [[ ! -d "$source_dir/.git" || ! -f "$source_dir/build.sh" ]]; then
    printf 'Missing checkout or build.sh: %s\n' "$repo" >&2
    exit 1
fi

out=$(mktemp -d "${TMPDIR:-/tmp}/opencpn-build-output.XXXXXX")
mkdir -p "$root/dist"
destination=$(mktemp -d "$root/dist/$repo.XXXXXX")
trap 'rmdir "$out" 2>/dev/null || true' EXIT
git -C "$source_dir" rev-parse HEAD > "$destination/source-commit.txt"
git -C "$source_dir" remote get-url origin > "$destination/source-url.txt"

image=opencpn-plugin-builder:ubuntu-26.04
docker build --platform linux/amd64 -t "$image" "$root" 2>&1 | tee "$destination/image.log"
status=0
docker run --rm --platform linux/amd64 --user "$(id -u):$(id -g)" \
    --mount "type=bind,src=$source_dir,dst=/source,readonly" \
    --mount "type=bind,src=$out,dst=/output" \
    --env "OPENCPN_BUILD_JOBS=${OPENCPN_BUILD_JOBS:-2}" \
    "$image" bash -euo pipefail -c '
        work=$(mktemp -d)
        cp -a /source/. "$work/"
        cd "$work"
        export OPENCPN_BUILD_DIR=build-container
        if [[ -e "$OPENCPN_BUILD_DIR" ]]; then
            export OPENCPN_BUILD_DIR=$(mktemp -d "$work/build-container.XXXXXX")
        fi
        marker=$(mktemp "$work/.build-start.XXXXXX")
        bash ./build.sh
        count=0
        while IFS= read -r -d "" package; do
            if tar -tzf "$package" | grep -E "(^|/)metadata[.]xml$" >/dev/null; then
                cp -- "$package" /output/
                count=$((count + 1))
            fi
        done < <(find . -name .git -prune -o -type f -name "*.tar.gz" -newer "$marker" -print0)
        if (( count == 0 )); then
            printf "Build produced no OpenCPN import tarball.\n" >&2
            exit 1
        fi
    ' 2>&1 | tee "$destination/build.log" || status=$?
shopt -s nullglob
for package in "$out"/*.tar.gz; do
    mv -- "$package" "$destination/"
done
printf 'Build output and logs: %s\n' "$destination"
exit "$status"

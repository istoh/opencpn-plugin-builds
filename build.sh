#!/usr/bin/env bash
# Fetch plugin sources and build them for every target this host can build.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
runner=(python3 "$root/scripts/build-target.py")

usage() {
    cat <<EOF
Usage: ./build.sh [options] [PLUGIN...]

Without PLUGIN, builds every plugin under plugins/.
  -t, --target NAME   build this target (repeatable). Default: all targets
                      runnable on this host. See ./build.sh --targets
      --targets       list targets and whether this host can build them
      --no-fetch      skip running the plugins' fetch.sh scripts
      --update        update existing checkouts while fetching
  -h, --help          show this help
Outputs go to dist/<target>/<plugin>/.
EOF
}

targets=()
plugins=()
fetch=1
fetch_args=()
while (( $# )); do
    case $1 in
        -t|--target) targets+=("${2:?--target needs a name}"); shift ;;
        --target=*) targets+=("${1#*=}") ;;
        --targets) "${runner[@]}" targets --runnable --why; exit ;;
        --no-fetch) fetch=0 ;;
        --update) fetch_args=(--update) ;;
        -h|--help) usage; exit ;;
        -*) usage >&2; exit 2 ;;
        *) plugins+=("$1") ;;
    esac
    shift
done

if (( ${#plugins[@]} == 0 )); then
    mapfile -t plugins < <("${runner[@]}" plugins)
    if (( ${#plugins[@]} == 0 )); then
        printf 'No plugins under plugins/. Add one with scripts/new-plugin.py.\n' >&2
        exit 1
    fi
fi
for plugin in "${plugins[@]}"; do
    if [[ $plugin == */* || ! -f $root/plugins/$plugin/build.sh ]]; then
        printf 'No plugins/%s/build.sh\n' "$plugin" >&2
        exit 2
    fi
done
if (( ${#targets[@]} == 0 )); then
    mapfile -t targets < <("${runner[@]}" targets --runnable --why)
fi

if (( fetch )); then
    "$root/fetch.sh" "${fetch_args[@]}" "${plugins[@]}"
fi

ok=()
failed=()
for target in "${targets[@]}"; do
    supported=$("${runner[@]}" plugins --target "$target")
    for plugin in "${plugins[@]}"; do
        if ! grep -qxF -- "$plugin" <<< "$supported"; then
            continue
        fi
        printf '\n=== %s / %s ===\n' "$target" "$plugin"
        if "${runner[@]}" build "$target" "$plugin"; then
            ok+=("$target/$plugin")
        else
            failed+=("$target/$plugin")
        fi
    done
done

printf '\nSucceeded: %d. Failed: %d.\n' "${#ok[@]}" "${#failed[@]}"
if (( ${#failed[@]} )); then
    for item in "${failed[@]}"; do
        printf '  %s  (logs: dist/%s/)\n' "$item" "$item"
    done
    exit 1
fi

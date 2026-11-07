#!/usr/bin/env bash
# Make an OpenCPN MBTiles overlay with satellite imagery over land and
# transparent water, in a GDAL container.
#
#   tools/land-overlay.sh --bbox 24.5,59.9,25.5,60.3 --zoom 8-14 --out helsinki.mbtiles
#
# See tools/land_overlay.py --help for all options. Downloads (land polygons,
# imagery tiles) are cached in ~/.cache/opencpn-plugin-builds/land-overlay.
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
image=${GDAL_IMAGE:-ghcr.io/osgeo/gdal:ubuntu-small-3.13.3}
read -ra docker <<< "${OPENCPN_DOCKER:-docker}"
cache=${XDG_CACHE_HOME:-$HOME/.cache}/opencpn-plugin-builds/land-overlay
mkdir -p "$cache"

# Mount the output's directory; pass the rest of the arguments through.
args=()
out_dir=$PWD
while (( $# )); do
    case $1 in
        --out) out=${2:?--out needs a file}; shift
               mkdir -p "$(dirname -- "$out")"
               out_dir=$(cd -- "$(dirname -- "$out")" && pwd)
               args+=(--out "/out/$(basename -- "$out")") ;;
        --land) land=${2:?--land needs a file or URL}; shift
                if [[ -e $land ]]; then
                    land_dir=$(cd -- "$(dirname -- "$land")" && pwd)
                    mounts=(--mount "type=bind,src=$land_dir,dst=/land,readonly")
                    args+=(--land "/land/$(basename -- "$land")")
                else
                    args+=(--land "$land")
                fi ;;
        *) args+=("$1") ;;
    esac
    shift
done

exec "${docker[@]}" run --rm --user "$(id -u):$(id -g)" \
    --mount "type=bind,src=$here/land_overlay.py,dst=/land_overlay.py,readonly" \
    --mount "type=bind,src=$cache,dst=/cache" \
    --mount "type=bind,src=$out_dir,dst=/out" \
    "${mounts[@]}" "$image" python3 /land_overlay.py "${args[@]}"

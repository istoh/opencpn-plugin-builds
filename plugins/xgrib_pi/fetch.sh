#!/usr/bin/env bash
# Source of the xGRIB plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/pob220/xgrib_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="xGRIB"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" xgrib_pi "$url" "$ref"

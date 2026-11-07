#!/usr/bin/env bash
# Source of the VDR plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/vdr_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="VDR"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" vdr_pi "$url" "$ref"

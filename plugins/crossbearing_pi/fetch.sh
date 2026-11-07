#!/usr/bin/env bash
# Source of the CrossBearing plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/g0kad/crossbearing_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="CrossBearing"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" crossbearing_pi "$url" "$ref"

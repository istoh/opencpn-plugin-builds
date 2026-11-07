#!/usr/bin/env bash
# Source of the Radar plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/opencpn-radar-pi/radar_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Radar"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" radar_pi "$url" "$ref"

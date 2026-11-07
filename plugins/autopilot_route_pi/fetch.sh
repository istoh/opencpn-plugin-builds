#!/usr/bin/env bash
# Source of the Autopilot Route plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/autopilot_route_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Autopilot Route"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" autopilot_route_pi "$url" "$ref"

#!/usr/bin/env bash
# Source of the IACFleet plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/nohal/iacfleet_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="IACFleet"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" iacfleet_pi "$url" "$ref"

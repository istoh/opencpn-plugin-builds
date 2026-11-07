#!/usr/bin/env bash
# Source of the DashboardSK plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/nohal/dashboardsk_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="DashboardSK"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" dashboardsk_pi "$url" "$ref"

#!/usr/bin/env bash
# Source of the DashboardTactics plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/dashboard_tactics_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="DashboardTactics"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" dashboard_tactics_pi "$url" "$ref"

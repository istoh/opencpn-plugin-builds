#!/usr/bin/env bash
# Source of the otidalplan plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rasbats/otidalplan_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="otidalplan"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" otidalplan_pi "$url" "$ref"

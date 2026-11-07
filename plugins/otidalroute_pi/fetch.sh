#!/usr/bin/env bash
# Source of the otidalroute plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rasbats/otidalroute_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="otidalroute"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" otidalroute_pi "$url" "$ref"

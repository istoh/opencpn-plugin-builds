#!/usr/bin/env bash
# Source of the sar plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rasbats/sar_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="sar"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" sar_pi "$url" "$ref"

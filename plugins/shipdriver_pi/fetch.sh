#!/usr/bin/env bash
# Source of the ShipDriver plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rasbats/shipdriver_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="ShipDriver"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" shipdriver_pi "$url" "$ref"

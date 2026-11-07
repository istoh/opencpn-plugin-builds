#!/usr/bin/env bash
# Source of the EarthExplorer plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rasbats/EarthExplorer_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="EarthExplorer"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" EarthExplorer_pi "$url" "$ref"

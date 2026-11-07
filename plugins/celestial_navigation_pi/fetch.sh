#!/usr/bin/env bash
# Source of the Celestial Navigation plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/celestial_navigation_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Celestial Navigation"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" celestial_navigation_pi "$url" "$ref"

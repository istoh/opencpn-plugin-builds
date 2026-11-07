#!/usr/bin/env bash
# Source of the Windvane plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/jongough/windvane_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Windvane"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" windvane_pi "$url" "$ref"

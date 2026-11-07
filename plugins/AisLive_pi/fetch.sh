#!/usr/bin/env bash
# Source of the AisLive plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Kupofty/AisLive_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="AisLive"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" AisLive_pi "$url" "$ref"

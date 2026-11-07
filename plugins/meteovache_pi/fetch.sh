#!/usr/bin/env bash
# Source of the MeteoVache plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rodemfr/meteovache_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="MeteoVache"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" meteovache_pi "$url" "$ref"

#!/usr/bin/env bash
# Source of the ObjSearch plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/nohal/objsearch_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="ObjSearch"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" objsearch_pi "$url" "$ref"

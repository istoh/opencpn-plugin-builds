#!/usr/bin/env bash
# Source of the Climatology plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/climatology_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Climatology"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" github.com--rgleason--climatology_pi "$url" "$ref"

#!/usr/bin/env bash
# Source of the Projections plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/nohal/projections_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Projections"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" projections_pi "$url" "$ref"

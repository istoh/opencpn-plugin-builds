#!/usr/bin/env bash
# Source of the Polar plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/polar_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Polar"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" polar_pi "$url" "$ref"

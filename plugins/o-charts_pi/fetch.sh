#!/usr/bin/env bash
# Source of the o-charts plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/bdbcat/o-charts_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="o-charts"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" o-charts_pi "$url" "$ref"

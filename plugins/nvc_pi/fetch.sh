#!/usr/bin/env bash
# Source of the NVCharts plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rasbats/nvc_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="NVCharts"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" nvc_pi "$url" "$ref"

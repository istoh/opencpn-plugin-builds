#!/usr/bin/env bash
# Source of the Deviation plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/Deviation_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Deviation"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" Deviation_pi "$url" "$ref"

#!/usr/bin/env bash
# Source of the NmeaConverter_pi plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/NmeaConverter_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="NmeaConverter_pi"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" NmeaConverter_pi "$url" "$ref"

#!/usr/bin/env bash
# Source of the NmeaGenerator plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Kupofty/NmeaGenerator_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="NmeaGenerator"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" NmeaGenerator_pi "$url" "$ref"

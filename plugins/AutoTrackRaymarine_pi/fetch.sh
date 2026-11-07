#!/usr/bin/env bash
# Source of the AutoTrackRaymarine plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/AutoTrackRaymarine_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="AutoTrackRaymarine"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" AutoTrackRaymarine_pi "$url" "$ref"

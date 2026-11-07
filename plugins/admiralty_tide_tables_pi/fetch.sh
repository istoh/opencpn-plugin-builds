#!/usr/bin/env bash
# Source of the Admiralty Tide Tables Calculation plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/admiralty_tide_tables_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Admiralty Tide Tables Calculation"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" admiralty_tide_tables_pi "$url" "$ref"

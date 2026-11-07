#!/usr/bin/env bash
# Source of the WeatherFax plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/weatherfax_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="WeatherFax"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" weatherfax_pi "$url" "$ref"

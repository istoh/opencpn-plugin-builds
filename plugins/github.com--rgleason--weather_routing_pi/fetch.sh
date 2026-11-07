#!/usr/bin/env bash
# Source of the WeatherRouting plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/weather_routing_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="WeatherRouting"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" github.com--rgleason--weather_routing_pi "$url" "$ref"

#!/usr/bin/env bash
# Source of the WeatherRouting plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/quinton-hoole/weather_routing_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" github.com--quinton-hoole--weather_routing_pi "$url" "$ref"

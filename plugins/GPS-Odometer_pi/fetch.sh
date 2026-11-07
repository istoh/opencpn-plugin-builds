#!/usr/bin/env bash
# Source of the GPS Odometer plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/rgleason/GPS-Odometer_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" GPS-Odometer_pi "$url" "$ref"

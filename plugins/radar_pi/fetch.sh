#!/usr/bin/env bash
# Source of the Radar plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/opencpn-radar-pi/radar_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" radar_pi "$url" "$ref"

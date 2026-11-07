#!/usr/bin/env bash
# Source of the AIS Radar view plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/rgleason/AISradar_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" AISradar_pi "$url" "$ref"

#!/usr/bin/env bash
# Source of the CrossBearing plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/g0kad/crossbearing_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" crossbearing_pi "$url" "$ref"

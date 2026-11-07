#!/usr/bin/env bash
# Source of the xGRIB plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/pob220/xgrib_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" xgrib_pi "$url" "$ref"

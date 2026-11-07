#!/usr/bin/env bash
# Source of the o-charts plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/bdbcat/o-charts_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" o-charts_pi "$url" "$ref"

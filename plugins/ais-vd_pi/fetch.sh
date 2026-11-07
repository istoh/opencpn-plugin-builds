#!/usr/bin/env bash
# Source of the ais-vd plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/Hakansv/ais-vd_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" ais-vd_pi "$url" "$ref"

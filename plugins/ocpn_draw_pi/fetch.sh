#!/usr/bin/env bash
# Source of the OCPN Draw plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/jongough/ocpn_draw_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" ocpn_draw_pi "$url" "$ref"

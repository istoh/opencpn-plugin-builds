#!/usr/bin/env bash
# Source of the Windvane plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/jongough/windvane_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" windvane_pi "$url" "$ref"

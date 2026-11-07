#!/usr/bin/env bash
# Source of the otidalplan plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/Rasbats/otidalplan_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" otidalplan_pi "$url" "$ref"

#!/usr/bin/env bash
# Source of the e_timer plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/Rasbats/e_timer_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" e_timer_pi "$url" "$ref"

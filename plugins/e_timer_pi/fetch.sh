#!/usr/bin/env bash
# Source of the e_timer plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rasbats/e_timer_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="e_timer"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" e_timer_pi "$url" "$ref"

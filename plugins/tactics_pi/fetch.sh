#!/usr/bin/env bash
# Source of the Tactics plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/tactics_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Tactics"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" tactics_pi "$url" "$ref"

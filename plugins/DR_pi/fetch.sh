#!/usr/bin/env bash
# Source of the DR plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rasbats/DR_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="DR"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" DR_pi "$url" "$ref"

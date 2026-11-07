#!/usr/bin/env bash
# Source of the otcurrent plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rasbats/otcurrent_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="otcurrent"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" otcurrent_pi "$url" "$ref"

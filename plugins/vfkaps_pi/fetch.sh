#!/usr/bin/env bash
# Source of the vfkaps plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rasbats/vfkaps_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="vfkaps"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" vfkaps_pi "$url" "$ref"

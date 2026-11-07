#!/usr/bin/env bash
# Source of the Engine_Dashboard plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/twocanplugin/enginedashboard.git
ref=@release
export OPENCPN_CATALOG_NAMES="Engine_Dashboard"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" enginedashboard "$url" "$ref"

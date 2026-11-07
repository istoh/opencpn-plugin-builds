#!/usr/bin/env bash
# Source of the StatusBar plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/statusbar_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="StatusBar"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" statusbar_pi "$url" "$ref"

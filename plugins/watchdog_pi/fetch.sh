#!/usr/bin/env bash
# Source of the Watchdog plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/watchdog_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Watchdog"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" watchdog_pi "$url" "$ref"

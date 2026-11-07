#!/usr/bin/env bash
# Source of the Launcher plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/nohal/launcher_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Launcher"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" launcher_pi "$url" "$ref"

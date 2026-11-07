#!/usr/bin/env bash
# Source of the Raymarine autopilot plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/raymarine_autopilot_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Raymarine autopilot"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" raymarine_autopilot_pi "$url" "$ref"

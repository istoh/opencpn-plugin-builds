#!/usr/bin/env bash
# Source of the pypilot plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/pypilot_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="pypilot"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" pypilot_pi "$url" "$ref"

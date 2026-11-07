#!/usr/bin/env bash
# Source of the Race Start Display plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/TwoCanPlugIn/RacingPlugin.git
ref=@release
export OPENCPN_CATALOG_NAMES="Race Start Display"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" RacingPlugin "$url" "$ref"

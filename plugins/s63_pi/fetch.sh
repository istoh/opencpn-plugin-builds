#!/usr/bin/env bash
# Source of the S63 plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/bdbcat/s63_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="S63"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" s63_pi "$url" "$ref"

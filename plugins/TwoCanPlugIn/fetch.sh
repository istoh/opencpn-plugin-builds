#!/usr/bin/env bash
# Source of the TwoCan Plugin plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/TwoCanPlugIn/TwoCanPlugIn.git
ref=@release
export OPENCPN_CATALOG_NAMES="TwoCan Plugin"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" TwoCanPlugIn "$url" "$ref"

#!/usr/bin/env bash
# Source of the CanadianTides plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rasbats/CanadianTides_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="CanadianTides"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" CanadianTides_pi "$url" "$ref"

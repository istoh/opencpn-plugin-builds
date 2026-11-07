#!/usr/bin/env bash
# Source of the UKTides plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rasbats/uktides_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="UKTides"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" uktides_pi "$url" "$ref"

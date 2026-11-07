#!/usr/bin/env bash
# Source of the Calculator plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rasbats/calculator_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Calculator"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" calculator_pi "$url" "$ref"

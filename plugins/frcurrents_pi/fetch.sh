#!/usr/bin/env bash
# Source of the frcurrents plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Rasbats/frcurrents_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="frcurrents"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" frcurrents_pi "$url" "$ref"

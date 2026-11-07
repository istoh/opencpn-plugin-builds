#!/usr/bin/env bash
# Source of the Logbook plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/LogbookKonni_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="Logbook"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" LogbookKonni_pi "$url" "$ref"

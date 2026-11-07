#!/usr/bin/env bash
# Source of the squiddio plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/rgleason/squiddio_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="squiddio"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" squiddio_pi "$url" "$ref"

#!/usr/bin/env bash
# Source of the javascript plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Antipole2/JavaScript_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="javascript"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" JavaScript_pi "$url" "$ref"

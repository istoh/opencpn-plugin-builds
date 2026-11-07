#!/usr/bin/env bash
# Source of the ais-vd plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/Hakansv/ais-vd_pi.git
ref=@release
export OPENCPN_CATALOG_NAMES="ais-vd"
# .gitmodules points at leamas/opencpn-libs, which lacks the pinned commit;
# OpenCPN/opencpn-libs has it.
export OPENCPN_SUBMODULE_URLS="opencpn-libs=https://github.com/OpenCPN/opencpn-libs.git"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" ais-vd_pi "$url" "$ref"

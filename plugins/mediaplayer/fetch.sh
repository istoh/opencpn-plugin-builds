#!/usr/bin/env bash
# Source of the Media_Player plugin.
# ref=@release builds the newest catalog release; a branch, tag or commit also works.
set -euo pipefail
url=https://github.com/twocanplugin/mediaplayer.git
ref=@release
export OPENCPN_CATALOG_NAMES="Media_Player"
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" mediaplayer "$url" "$ref"

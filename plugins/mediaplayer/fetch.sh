#!/usr/bin/env bash
# Source of the Media_Player plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/twocanplugin/mediaplayer.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" mediaplayer "$url" "$ref"

#!/usr/bin/env bash
# Source of the Engine_Dashboard plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/twocanplugin/enginedashboard.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" enginedashboard "$url" "$ref"

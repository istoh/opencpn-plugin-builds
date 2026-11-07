#!/usr/bin/env bash
# Source of the TwoCan Plugin plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/TwoCanPlugIn/TwoCanPlugIn.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" TwoCanPlugIn "$url" "$ref"

#!/usr/bin/env bash
# Source of the Race Start Display plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/TwoCanPlugIn/RacingPlugin.git
# master is unreleased work that needs a newer plugin API; v1.1 is the catalog release.
ref=v1.1
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" RacingPlugin "$url" "$ref"

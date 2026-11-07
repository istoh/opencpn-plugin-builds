#!/usr/bin/env bash
# Source of the S63 plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/bdbcat/s63_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" s63_pi "$url" "$ref"

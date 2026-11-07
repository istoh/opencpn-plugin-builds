#!/usr/bin/env bash
# Source of the vfkaps plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/Rasbats/vfkaps_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" vfkaps_pi "$url" "$ref"

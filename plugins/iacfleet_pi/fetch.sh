#!/usr/bin/env bash
# Source of the IACFleet plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/nohal/iacfleet_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" iacfleet_pi "$url" "$ref"

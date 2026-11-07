#!/usr/bin/env bash
# Source of the NmeaConverter_pi plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/rgleason/NmeaConverter_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" NmeaConverter_pi "$url" "$ref"

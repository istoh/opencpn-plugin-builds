#!/usr/bin/env bash
# Source of the CanadianTides plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/Rasbats/CanadianTides_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" CanadianTides_pi "$url" "$ref"

#!/usr/bin/env bash
# Source of the Admiralty Tide Tables Calculation plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/rgleason/admiralty_tide_tables_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" admiralty_tide_tables_pi "$url" "$ref"

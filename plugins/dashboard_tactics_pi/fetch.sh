#!/usr/bin/env bash
# Source of the DashboardTactics plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/rgleason/dashboard_tactics_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" dashboard_tactics_pi "$url" "$ref"

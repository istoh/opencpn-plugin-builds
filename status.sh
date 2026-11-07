#!/usr/bin/env bash
# Upstream status of the plugins: newest release, commits since, release cadence,
# milestones and our build. Usage: ./status.sh [--opencpn 5.12.4] [PLUGIN...]
set -euo pipefail
exec python3 "$(dirname -- "${BASH_SOURCE[0]}")/scripts/status.py" "$@"

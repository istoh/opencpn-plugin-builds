#!/usr/bin/env bash
# Update all plugin checkouts in repos/ (git pull, or move to the pinned ref).
# Missing checkouts are cloned. Usage: ./update.sh [PLUGIN...]
set -euo pipefail
exec "$(dirname -- "${BASH_SOURCE[0]}")/fetch.sh" --update "$@"

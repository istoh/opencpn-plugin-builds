#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec python3 "$root/build-target.py" build "${OPENCPN_TARGET:-ubuntu-26.04-x64}" "$@"

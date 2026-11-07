#!/usr/bin/env bash
# Source of the WhereIsMyBoat plugin.
# Not in the OpenCPN catalog yet, so the default branch is built.
set -euo pipefail
url=https://github.com/istoh/whereismyboat_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" whereismyboat_pi "$url" "$ref"

#!/usr/bin/env bash
# Source of the javascript plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/Antipole2/JavaScript_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" JavaScript_pi "$url" "$ref"

#!/usr/bin/env bash
# Source of the frcurrents plugin. Set ref to a branch, or pin a tag or commit for reproducible builds.
set -euo pipefail
url=https://github.com/Rasbats/frcurrents_pi.git
ref=
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/git-fetch.sh" frcurrents_pi "$url" "$ref"

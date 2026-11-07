#!/usr/bin/env bash
# On the host: plugins/objsearch_pi/build.sh [-t TARGET]... builds this plugin in
# the target containers (see ./build.sh --help).
# In the container, the recipe below runs in a scratch copy of repos/objsearch_pi.
# Environment: OPENCPN_TARGET, OPENCPN_TARGET_TUPLE, OPENCPN_BUILD_JOBS,
# OPENCPN_BUILD_DIR, OPENCPN_PLUGIN_DIR (this directory), OPENCPN_SCRIPTS.
# Leave the import tarball (*.tar.gz with metadata.xml) anywhere in the tree.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/../../scripts/plugin-entry.sh"

cmake_plugin

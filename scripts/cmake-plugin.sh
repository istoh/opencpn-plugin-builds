#!/usr/bin/env bash
# Default recipe for plugins based on the OpenCPN plugin templates:
# configure, build and run the "tarball" target. Extra arguments go to cmake.
set -euo pipefail
if [[ ! -f CMakeLists.txt ]]; then
    printf 'No root CMakeLists.txt. Write a custom plugins/<name>/build.sh.\n' >&2
    exit 1
fi
args=(-DCMAKE_BUILD_TYPE=Release)
if [[ -n ${OPENCPN_TARGET_TUPLE:-} ]]; then
    args+=("-DOCPN_TARGET_TUPLE=$OPENCPN_TARGET_TUPLE")
fi
build_dir=${OPENCPN_BUILD_DIR:-build}
cmake -S . -B "$build_dir" "${args[@]}" "$@"
cmake --build "$build_dir" --config Release --parallel "${OPENCPN_BUILD_JOBS:-2}"
# Newer plugin templates already create the tarball in the default build.
if [[ -z $(find "$build_dir" -maxdepth 1 -name '*.tar.gz' -print -quit) ]]; then
    cmake --build "$build_dir" --config Release --target tarball
fi

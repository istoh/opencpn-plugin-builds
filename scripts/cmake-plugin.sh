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
if [[ ${OPENCPN_TARGET:-} == android-* ]]; then
    # Cross-compile with the plugin's own toolchain file. Templates name the
    # arm64 one either android-aarch64 or android-arm64.
    arch=${OPENCPN_TARGET#android-}
    toolchain=
    for candidate in "cmake/android-${arch/arm64/aarch64}-toolchain.cmake" "cmake/android-$arch-toolchain.cmake"; do
        if [[ -f $candidate ]]; then
            toolchain=$PWD/$candidate
            break
        fi
    done
    if [[ -z $toolchain ]]; then
        printf 'No cmake/android-*-toolchain.cmake: this plugin has no Android build.\n' >&2
        exit 1
    fi
    export OCPN_TARGET=$OPENCPN_TARGET
    args+=("-DCMAKE_TOOLCHAIN_FILE=$toolchain")
# The NDK hardens by default. Debian's compiler, unlike Ubuntu's, does not.
# Use the same flags on all Linux builds. CMake reads these on the first configure.
elif [[ $(uname -s) == Linux ]]; then
    hardening="-fstack-protector-strong -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=2"
    export CFLAGS="$hardening ${CFLAGS:-}" CXXFLAGS="$hardening ${CXXFLAGS:-}"
    export LDFLAGS="-Wl,-z,relro,-z,now ${LDFLAGS:-}"
fi
build_dir=${OPENCPN_BUILD_DIR:-build}
cmake -S . -B "$build_dir" "${args[@]}" "$@"
cmake --build "$build_dir" --config Release --parallel "${OPENCPN_BUILD_JOBS:-2}"
# Newer plugin templates already create the tarball in the default build.
if [[ -z $(find "$build_dir" -maxdepth 1 -name '*.tar.gz' -print -quit) ]]; then
    cmake --build "$build_dir" --config Release --target tarball
fi

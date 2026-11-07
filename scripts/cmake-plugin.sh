#!/usr/bin/env bash
# Default recipe for plugins based on the OpenCPN plugin templates: configure,
# build and create the import tarball. Extra arguments go to cmake.
# Newer templates have a "tarball" target. Older ones build a CPack package,
# and their CI adds metadata.xml to it; the same is done here.
set -euo pipefail
if [[ ! -f CMakeLists.txt ]]; then
    printf 'No root CMakeLists.txt. Write a custom plugins/<name>/build.sh.\n' >&2
    exit 1
fi
build_dir=${OPENCPN_BUILD_DIR:-build}
# CMake 4 refuses projects that declare compatibility with CMake < 3.5.
args=(-DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5)
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
            toolchain=$candidate
            break
        fi
    done
    if [[ -z $toolchain ]]; then
        printf 'No cmake/android-*-toolchain.cmake: this plugin has no Android build.\n' >&2
        exit 1
    fi
    # Some toolchain files ask for API level 16, below what current NDKs support.
    mkdir -p "$build_dir"
    sed -E 's/(CMAKE_SYSTEM_VERSION[[:space:]]+)1[0-9]\b/\121/' "$toolchain" > "$build_dir/android-toolchain.cmake"
    export OCPN_TARGET=$OPENCPN_TARGET
    common=/opt/android/cache
    # Plugins resolve wxWidgets symbols from OpenCPN at load time, but current
    # NDKs reject undefined symbols in shared libraries by default.
    args+=("-DCMAKE_TOOLCHAIN_FILE=$(cd -- "$build_dir" && pwd)/android-toolchain.cmake"
           "-DOCPN_ANDROID_CACHEDIR=$common" -DANDROID_ALLOW_UNDEFINED_SYMBOLS=ON)
    if grep -qs 'androideabi-qt' cmake/PluginSetup.cmake; then
        # Older templates select Android by the wxWidgets configuration name.
        if [[ $arch == arm64 ]]; then
            qt=build_arm64/qtbase wxqt=build_android_release_64_static_O3
        else
            qt=build_arm32_19_O3/qtbase wxqt=build_android_release_19_static_O3
        fi
        # They expect the libraries at a path relative to the source tree.
        ln -sfn "$common/OCPNAndroidCommon-master" OCPNAndroidCommon-master
        args+=("-D_wx_selected_config=androideabi-qt-$arch" "-DQt_Build=$qt" "-DwxQt_Build=$wxqt"
               -DOCPN_Android_Common=OCPNAndroidCommon-master)
    fi
elif [[ $(uname -s) == Linux ]]; then
    # The NDK hardens by default. Debian's compiler, unlike Ubuntu's, does not.
    # Use the same flags on all Linux builds. CMake reads these on the first
    # configure. GCC 15 no longer includes <cstdint> transitively, which older
    # plugin code relies on.
    hardening="-fstack-protector-strong -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=2"
    export CFLAGS="$hardening ${CFLAGS:-}"
    export CXXFLAGS="$hardening -include cstdint ${CXXFLAGS:-}"
    export LDFLAGS="-Wl,-z,relro,-z,now ${LDFLAGS:-}"
fi

cmake -S . -B "$build_dir" "${args[@]}" "$@"
cmake --build "$build_dir" --config Release --parallel "${OPENCPN_BUILD_JOBS:-2}"

# Read the whole list first: grep -q would stop early and fail the pipe.
build_targets=$(cmake --build "$build_dir" --target help 2>/dev/null || true)
has_target() {
    grep -Eq "(^|[[:space:]])$1([[:space:]:]|$)" <<< "$build_targets"
}
tarballs() {
    find "$build_dir" -maxdepth 1 -name '*.tar.gz' -print
}
# Newer templates already create the tarball in the default build.
if [[ -z $(tarballs) ]]; then
    if has_target tarball; then
        cmake --build "$build_dir" --config Release --target tarball
    elif has_target package; then
        cmake --build "$build_dir" --config Release --target package
        metadata=$(find "$build_dir" -maxdepth 1 -name '*.xml' -print -quit)
        if [[ -z $metadata ]]; then
            printf 'CPack package built, but no plugin XML to use as metadata.xml.\n' >&2
            exit 1
        fi
        # Put metadata.xml at the top of each CPack tarball, as the template's
        # cloudsmith-upload.sh does.
        while IFS= read -r package; do
            staging=$(mktemp -d)
            tar -xzf "$package" -C "$staging"
            rm -rf "$staging/root"
            cp "$metadata" "$staging/metadata.xml"
            package=$(cd -- "$(dirname -- "$package")" && pwd)/$(basename -- "$package")
            (cd "$staging" && tar -czf "$package" -- *)
            rm -rf "$staging"
        done < <(tarballs)
    else
        printf 'Neither a "tarball" nor a "package" target.\n' >&2
        exit 1
    fi
fi

# Android cross-compilation environment. The NDK version and its SHA-1 come
# from the target's build_args in targets.json, so an older NDK can be added
# as another target.
ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE}

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates cmake curl file gettext git ninja-build \
    pkg-config python3 unzip \
    && rm -rf /var/lib/apt/lists/*

ARG NDK_VERSION=r30
ARG NDK_SHA1=5107f898313790e449e87eee2183d9a20602dee9
RUN curl -fsSL --retry 3 -o /tmp/ndk.zip \
        "https://dl.google.com/android/repository/android-ndk-${NDK_VERSION}-linux.zip" \
    && echo "${NDK_SHA1}  /tmp/ndk.zip" | sha1sum -c - \
    && mkdir -p /opt/android \
    && unzip -q /tmp/ndk.zip -d /opt/android \
    && mv "/opt/android/android-ndk-${NDK_VERSION}" /opt/android/ndk \
    && rm /tmp/ndk.zip

# The plugin toolchain files look for NDK_HOME, falling back to /opt/android/ndk.
ENV NDK_HOME=/opt/android/ndk ANDROID_NDK_HOME=/opt/android/ndk HOME=/tmp

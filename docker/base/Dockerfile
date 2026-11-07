ARG BASE_IMAGE=ubuntu:26.04
FROM ${BASE_IMAGE}

# Common plugin dependencies, collected from the plugins' ci/control files.
# lsb-release is used by the older plugin templates to detect the distribution.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates cmake curl file gettext git libarchive-dev \
    libbz2-dev libcairo2-dev libcurl4-openssl-dev libelf-dev libexif-dev \
    libgl-dev libglu1-mesa-dev libgtk-3-dev liblz4-dev liblzma-dev \
    libpango1.0-dev libsqlite3-dev libssl-dev libwxgtk3.2-dev lsb-release \
    ninja-build pkg-config portaudio19-dev python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Packages that are missing or renamed in some releases: install what exists.
RUN apt-get update \
    && wanted="libgdk-pixbuf-2.0-dev libglew-dev libjsoncpp-dev libtinyxml-dev \
        libunarr-dev libwxgtk-webview3.2-dev libwxsvg-dev" \
    && available=$(for package in $wanted; do \
        apt-cache show "$package" >/dev/null 2>&1 && echo "$package"; done) \
    && apt-get install -y --no-install-recommends $available \
    && rm -rf /var/lib/apt/lists/*

ENV HOME=/tmp

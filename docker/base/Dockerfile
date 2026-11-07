ARG BASE_IMAGE=ubuntu:26.04
FROM ${BASE_IMAGE}

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates cmake curl gettext git libarchive-dev \
    libcurl4-openssl-dev libgl-dev libglu1-mesa-dev libgtk-3-dev \
    libwxgtk3.2-dev ninja-build pkg-config python3 \
    && rm -rf /var/lib/apt/lists/*

ENV HOME=/tmp

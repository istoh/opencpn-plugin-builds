ARG BASE_IMAGE=ubuntu:26.04
FROM ${BASE_IMAGE}

RUN apt-get update && apt-get install -y --no-install-recommends cppcheck \
    && rm -rf /var/lib/apt/lists/*

ENV HOME=/tmp

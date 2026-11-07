# OpenCPN plugin builds

This repository builds OpenCPN plugin sources from the official master catalog
for Ubuntu 26.04 x86-64. Each build runs in a separate container using the
shared Docker image. The compiled plugin tarballs can be tested using
**Options → Plugins → Import Plugin Tarball** in OpenCPN.

## Local build

Docker, Git, Bash and Python 3 are required.

```sh
./fetch.sh --match DashboardSK
./container-build.sh dashboardsk_pi
```

Look under `dist/` for the package, source revision and logs. Each run gets
its own output directory. The source checkout is mounted read-only. For a
native build without Docker, run `./build.sh dashboardsk_pi`.

Run `./fetch.sh --list` to preview the full catalog or `./fetch.sh` to
clone it. The fetcher leaves existing checkout revisions and build scripts
in place. It reports entries without a recognized public Git source.

## GitHub Actions

Open **Actions → Build OpenCPN plugins → Run workflow**. The default filter
builds DashboardSK. Clear it to try all catalog repositories. Each matrix job
uploads its own package and logs. Some repositories need extra dependencies
or custom build commands. A successful package still needs a load test in
the target OpenCPN installation.

## Build targets

```sh
python3 build-target.py list
python3 build-target.py build rpi-trixie-arm64 dashboardsk_pi
```

Select one target per Actions run. Linux profiles cover Ubuntu and Debian
x86-64 plus Debian 12 Bookworm and Debian 13 Trixie on ARM for Raspberry
Pi OS. An x86-64 machine needs Docker ARM emulation for local Raspberry
Pi builds. Actions uses ARM runners for arm64 and QEMU for armhf. The
32-bit builds target ARMv7 and newer Raspberry Pi CPUs. Pi 1 and the
original Pi Zero need a separate ARMv6 build environment.

Windows and macOS profiles run natively. They provide runner selection and
artifact collection. The default CMake path requires the plugin's native
development dependencies. Add a plugin-specific
`overrides/<checkout>/<target>/build.sh` for custom setup and packaging,
or a `Dockerfile` at the same path for a Linux image override. Linux
overrides receive the selected `BASE_IMAGE` build argument. Declare extra
targets in `targets.json`. Validate a package in the exact OpenCPN and OS
version before relying on it.

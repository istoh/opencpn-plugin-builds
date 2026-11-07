# OpenCPN plugin builds

Builds OpenCPN plugins for several platforms. Linux builds always run in
containers. Each plugin gets its own fetch and build recipe in this
repository. Plugin sources stay in separate checkouts that are never
committed here.

```
build.sh                  fetch + build everything (or the named plugins)
fetch.sh                  run the plugins' fetch.sh scripts only
update.sh                 git pull every checkout (fetch.sh --update)
images.sh                 build the container environments only
status.sh                 upstream status: releases, commits since, cadence
targets.json              build targets: base image, platform, OpenCPN tuple
docker/base/Dockerfile    shared image with the common build dependencies
plugins/<name>/
    fetch.sh              where the source comes from (URL, ref, catalog names)
    build.sh              on the host: builds this plugin in the containers;
                          inside a container: the build recipe
    Dockerfile            optional: extra dependencies on top of the base image
    targets               optional: limit the targets (names or globs, ! excludes)
scripts/                  shared helpers (runner, git fetch, default CMake recipe)
repos/<name>/             source checkouts (git-ignored)
dist/<target>/<name>/     tarballs, logs and source revision (git-ignored)
```

## Usage

Docker, Git, Bash and Python 3 are required. If Docker needs root on
this machine, set `OPENCPN_DOCKER="sudo docker"`. The containers still run
as your user, so the outputs stay yours.

```sh
./images.sh                         # build the environments (only those that changed)
./build.sh                          # all plugins, all targets this host can build
./build.sh dashboardsk_pi           # one plugin
plugins/dashboardsk_pi/build.sh     # the same, run from the plugin directory
./build.sh -t rpi-trixie-arm64      # one target (repeatable)
./build.sh --targets                # which targets this host can build, and why not
./build.sh --no-fetch               # use the existing checkouts as they are
./update.sh                         # git pull all checkouts (or move to the pinned ref)
```

The images contain only the build environment. A plugin is compiled with
`docker run`: the repository root is mounted read-only at `/work` (so
`repos/<name>/` is `/work/repos/<name>/`), and only
`dist/<target>/<name>/` is writable. Each image is tagged with a hash of
its Dockerfile, its directory and its base image. An image is rebuilt only
when one of these changes. Otherwise the existing environment is reused.
`./images.sh --rebuild` forces a rebuild, for example to pick up
distribution updates.

Test a result with **Options → Plugins → Import Plugin Tarball** in OpenCPN.
Each run replaces the contents of `dist/<target>/<plugin>/`.

On x86-64, the Raspberry Pi targets need QEMU emulation, installed once
per boot:

```sh
sudo docker run --privileged --rm tonistiigi/binfmt --install arm64,arm
```

## Adding a plugin

`plugins/` holds one directory for every Git source in the OpenCPN master
catalog. Logbook and VDR have no source in the catalog and are mapped by
hand in `scripts/new-plugin.py`. Re-run the script to pick up new catalog
entries. Existing directories are kept.

```sh
python3 scripts/new-plugin.py --list --match Weather   # search the OpenCPN catalog
python3 scripts/new-plugin.py --match WeatherRouting   # create plugins/<name>/
```

This creates a `fetch.sh` and a `build.sh` that uses the default
`scripts/cmake-plugin.sh` recipe. That recipe works for plugins based on
the OpenCPN plugin templates. Otherwise, edit `build.sh` to follow the
upstream build instructions. Set `ref=` in `fetch.sh` to a tag or commit
for a reproducible build.

`build.sh` runs in a writable scratch copy of `repos/<name>/`. The
original checkout is mounted read-only. These variables are available:

| Variable | Meaning |
| --- | --- |
| `OPENCPN_TARGET` | target name from `targets.json` |
| `OPENCPN_TARGET_TUPLE` | `target;version;arch` for `-DOCPN_TARGET_TUPLE` |
| `OPENCPN_BUILD_JOBS` | parallel jobs |
| `OPENCPN_BUILD_DIR` | empty build directory |
| `OPENCPN_PLUGIN_DIR` | `plugins/<name>/` (for patches and other files) |
| `OPENCPN_SCRIPTS` | the shared `scripts/` directory |

The build only needs to leave an import tarball (a `*.tar.gz` that contains
`metadata.xml`) somewhere in the tree. Each tarball is checked against the
target's tuple.

`scripts/cmake-plugin.sh` handles both the newer templates, which have a
`tarball` target, and the older ones, which build a CPack package and get
`metadata.xml` from their CI. For Android, it uses the plugin's toolchain
file and the prebuilt `OCPNAndroidCommon` libraries in the Android image.

To limit a plugin to some targets, list them in `plugins/<name>/targets`,
one name or glob per line. A line starting with `!` excludes targets:

```
# No Android toolchain file upstream.
!android-*
```

When an upstream `.gitmodules` points at a repository that lacks the pinned
submodule commit, `fetch.sh` can fetch it elsewhere with
`OPENCPN_SUBMODULE_URLS="<name>=<url>"` (see `plugins/ais-vd_pi/fetch.sh`).
When the default branch is unreleased work, pin `ref=` to the release tag
(see `plugins/RacingPlugin/fetch.sh`).

To add extra packages, create a `plugins/<name>/Dockerfile`:

```dockerfile
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
RUN apt-get update && apt-get install -y --no-install-recommends libfoo-dev \
    && rm -rf /var/lib/apt/lists/*
```

## Targets

| Target | How it builds |
| --- | --- |
| `ubuntu-26.04-x64`, `ubuntu-24.04-x64`, `debian-13-x64` | container |
| `rpi-trixie-arm64/armhf`, `rpi-bookworm-arm64/armhf` | container, ARM (QEMU on x86-64) |
| `android-arm64`, `android-armhf` | container, cross-compiled with the Android NDK |
| `windows-x64`, `macos-arm64`, `macos-x64` | natively on a matching host or GitHub runner |

Android builds use `docker/android`. The NDK version and its SHA-1 are
`build_args` of the target in `targets.json` (now r30, the latest stable
release). To support an older NDK, add another target with different
`build_args`. The recipe uses the plugin's own
`cmake/android-*-toolchain.cmake`.

To give a target its own image instead of `docker/base`, set
`"dockerfile": "docker/<name>/Dockerfile"` in `targets.json`. The 32-bit
ARM builds target ARMv7 and newer. Pi 1 and the original Pi Zero would need
a separate ARMv6 environment.

## Released versions

`ref=@release` in `fetch.sh` (the default) builds the newest release of the
plugin in the OpenCPN catalog. The plugin is found by the names in
`OPENCPN_CATALOG_NAMES`. The release is matched to a Git tag such as `v1.2`,
`1.2.0.0` or `name-1.2`, or to the commit in a version like `2.0+132.ebb1fdf`.
Without a match, the default branch is built with a warning. A pinned tag
that is older than the newest release also gives a warning. The warnings are
shown in the build plan and the release notes. When an author publishes a
new release in the catalog, the next run builds it.

Each built package is compared with the official catalog package for the
same target (or the nearest Debian/Ubuntu one):

```sh
python3 scripts/compare.py dashboardsk_pi ubuntu-24.04-x64
```

The packages are never byte-identical. The comparison reports the version,
the plugin API, the file list and, for each shared library, its NEEDED
libraries, the `create_pi`/`destroy_pi` entry points and the exported
symbols (without the standard library and wxWidgets inlines).

A plugin is built for a plugin API version, not an OpenCPN version. The API
version comes from the plugin's `api-version` metadata:

| Plugin API | Needs OpenCPN |
|---|---|
| 1.16 | 5.0 |
| 1.17 | 5.2 |
| 1.18 | 5.8 |
| 1.19, 1.20 | 5.12 |
| 1.21, 1.22 | 5.14 |

## Status

```sh
./status.sh --opencpn 5.12.4
```

For each plugin, the status table shows:

- the newest catalog release and the OpenCPN it needs (⚠ when newer than
  `--opencpn`)
- when it was released and how many commits the default branch has gained
  since then
- the median interval between its GitHub releases and the next open
  milestone with a due date
- our build, from the `current` release manifest

The build plan in Actions and the `current` release show the same table.

## Analysis

```sh
python3 scripts/analyze.py dashboardsk_pi dist/*/dashboardsk_pi/*.tar.gz
```

Runs the following checks and writes the reports to
`dist/analysis/<plugin>/`:

- **cppcheck:** static analysis, run in the `docker/analysis` image.
- **OSV-Scanner:** known vulnerabilities in submodules and bundled libraries.
- **Trivy:** vulnerabilities and committed secrets.
- **ELF hardening check:** RELRO, non-executable stack, stack protector and
  FORTIFY in each shared library of the given tarballs.

The scanner images are pinned in `scripts/analyze.py`. Findings are
informational and never fail a build.

## GitHub Actions

`.github/workflows/build.yml` runs nightly and on demand from
**Actions → Build OpenCPN plugins → Run workflow**:

1. **plan** reads `manifest.json` from the `current` release and resolves
   each plugin's upstream commit with `git ls-remote`, without cloning. For
   every plugin and target it computes a key from the commit, the plugin
   recipe, the shared scripts and the build environment. Only builds whose
   key changed are run. A build that failed with the same key is not retried
   until something changes, or until it is run with *retry failed*.
2. **build** runs one job per plugin and runner. It clones the plugin onto the
   runner and builds the changed targets in the containers. Arm64 builds
   use the `ubuntu-24.04-arm` runner. Armhf builds use QEMU on x86-64. When
   the commit is new, the job also runs the source scans.
3. **publish** creates a dated `builds-YYYYMMDD-HHMM` release with the new
   tarballs, the release notes and `analysis.tar.gz`. The notes list the
   version, the upstream commits since the previous build and the analysis
   summary. It also updates the `current` release, which always holds the
   newest package of every plugin and target plus `manifest.json`.

The run inputs select plugins and targets: `containers` (default), `all`, or
target names. *force* rebuilds everything selected. Build logs are kept as
workflow artifacts for 30 days.

## Satellite land overlay

`tools/land-overlay.sh` creates an OpenCPN chart overlay. It shows satellite
imagery over land and leaves water transparent, so the nautical chart shows
at sea:

```sh
tools/land-overlay.sh --bbox 24.5,59.9,25.5,60.3 --zoom 8-14 --out helsinki.mbtiles
```

It runs in a GDAL container and makes an MBTiles file with
`type=overlay`. OpenCPN draws such a file above the other charts:

- **Imagery:** Sentinel-2 cloudless 2025 by EOX (10 m, sharp to about
  zoom 14, CC BY-NC-SA 4.0, so non-commercial use only). `--source` takes
  another XYZ tile URL, if its terms allow offline use.
- **Water mask:** ESA WorldCover 2021 (10 m, CC BY 4.0). Water class 80,
  lakes included, is transparent. `--land osm` uses the OpenStreetMap land
  polygons instead (an 800 MB download, keeps lakes), and `--land FILE`
  uses your own polygons.
- **Zoom levels:** OpenCPN draws only the overlay's tiles for the current
  zoom level, so every level in `--zoom` is generated. More than 20,000
  tiles needs `--yes`.
- **Cache:** Downloads are kept in `~/.cache/opencpn-plugin-builds/land-overlay`.

Add the directory containing the `.mbtiles` file in **Options → Charts →
Chart Files**. OpenCPN may hide a large MBTiles overlay at startup. Show it
by clicking it in the chart bar at the bottom of the window.

## License

The build scripts and recipes in this repository are under the MIT License
(see `LICENSE`). The plugins and their packages keep their upstream licenses,
mostly GPL. Each source is listed in the plugin's `fetch.sh`, and its exact
commit is recorded with each build.

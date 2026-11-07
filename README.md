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

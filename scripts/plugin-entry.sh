# Sourced by every plugins/<name>/build.sh.
# On the host it hands over to the top-level build.sh, which starts the
# target containers for this plugin; the arguments are passed on, so
# "plugins/<name>/build.sh -t rpi-trixie-arm64" works. Inside a build
# container (OPENCPN_TARGET is set) it returns and the recipe below runs.
if [[ -z ${OPENCPN_TARGET:-} ]]; then
    plugin_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[1]}")" && pwd)
    exec "$plugin_dir/../../build.sh" "$@" "$(basename -- "$plugin_dir")"
fi

# Default recipe for plugins based on the OpenCPN plugin templates.
cmake_plugin() {
    bash "$OPENCPN_SCRIPTS/cmake-plugin.sh" "$@"
}

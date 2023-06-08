#!/bin/bash
set -eo pipefail
shopt -s nullglob

# logging functions
_log() {
    local type="$1"
    shift
    printf '%s [%s] [Entrypoint]: %s\n' "$(date +"%Y/%m/%d %H:%M:%S")" "$type" "$*"
}

_note() {
    _log Note "$@"
}

_warn() {
    _log Warn "$@" >&2
}

_error() {
    _log ERROR "$@" >&2
    exit 1
}

# check to see if this file is being run or sourced from another script
_is_sourced() {
    # https://unix.stackexchange.com/a/215279
    [ "${#FUNCNAME[@]}" -ge 2 ] \
        && [ "${FUNCNAME[0]}" = '_is_sourced' ] \
        && [ "${FUNCNAME[1]}" = 'source' ]
}

function init_supervisor() {
    if [ ! -d "/var/log/supervisor/" ]; then
        mkdir -p /var/log/supervisor/
    fi
    if [ ! -d "/var/run/supervisor/" ]; then
        mkdir -p /var/run/supervisor/
    fi
    if [ ! -L "/etc/supervisor" ] && [ "$(readlink /etc/supervisor)" != "/app/supervisor" ]; then
        if [ -f "/etc/supervisor" ];then
            mv /etc/supervisor /etc/supervisor."$(date +%s)"
        fi
        ln -s /app/supervisor /etc/supervisor
    fi
}

function service_initialize() {
    init_supervisor
}

function env_initialize() {
    # custom env init script. file place source directory, so we can cache docker layout
    if [ -f "/app/program/init.sh" ]; then
        source /app/program/init.sh
    fi
}

_main() {
    env_initialize
    service_initialize
    exec "$@"
}

# If we are sourced from elsewhere, don't perform any further actions
if ! _is_sourced; then
    _main "$@"
fi
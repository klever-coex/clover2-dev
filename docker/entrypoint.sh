#!/bin/bash
set -e

if [ -n "${HOST_UID}" ] && [ -n "${HOST_GID}" ]; then
    usermod -u "${HOST_UID}" "${USERNAME}" >/dev/null 2>&1 || true
    groupmod -g "${HOST_GID}" "${USERNAME}" >/dev/null 2>&1 || true
fi

# shellcheck source=/dev/null
source "/opt/ros/${ROS_DISTRO}/setup.bash"

if [ -f "/home/${USERNAME}/ws/install/setup.bash" ]; then
    # shellcheck source=/dev/null
    source "/home/${USERNAME}/ws/install/setup.bash"
fi

exec gosu "${USERNAME}" "$@"

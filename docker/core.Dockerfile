ARG BASE_IMAGE=clover2-base

FROM ${BASE_IMAGE} AS ansible

ENV UV_TOOL_DIR=/opt/uv/tools \
    UV_TOOL_BIN_DIR=/opt/uv/bin

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,id=uv-cache,target=/root/.cache/uv \
    uv tool install \
      --python-preference only-system \
      --with-executables-from "ansible-core" \
      "ansible==10.*"

FROM ${BASE_IMAGE} AS core-depend
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG ROS_DISTRO
ARG ROS_PACKAGES_PROFILE=jazzy-2026-06-18

USER ${USERNAME}
WORKDIR /home/${USERNAME}

RUN --mount=type=bind,from=ansible,source=/opt/uv,target=/opt/uv \
    --mount=type=bind,source=ansible-galaxy-requirements.yaml,target=/tmp/ansible/ansible-galaxy-requirements.yaml \
    --mount=type=bind,source=ansible,target=/tmp/ansible/ansible \
    --mount=type=cache,id=apt-cache-${ROS_DISTRO},target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lists-${ROS_DISTRO},target=/var/lib/apt/lists,sharing=locked \
    export PATH="/opt/uv/bin:${PATH}" && \
    cd /tmp/ansible && \
    ansible-galaxy collection install -f -r ansible-galaxy-requirements.yaml && \
    ansible-playbook clover2.dev.install_deps --tags core -i /tmp/ansible/ansible/inventory.ini \
    -e rosdistro=${ROS_DISTRO} -e ros_packages_profile=${ROS_PACKAGES_PROFILE}

USER root

RUN rosdep update --rosdistro=${ROS_DISTRO} -r

COPY --parents --chown=${USERNAME}:${USERNAME} src/**/package.xml /tmp/clover2-dev

RUN --mount=type=cache,id=apt-cache-${ROS_DISTRO},target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lists-${ROS_DISTRO},target=/var/lib/apt/lists,sharing=locked \
    apt-get update && \
    . "/opt/ros/${ROS_DISTRO}/setup.sh" && \
    rosdep install -y --from-paths /tmp/clover2-dev/src \
    --ignore-src \
    --rosdistro "${ROS_DISTRO}"

FROM core-depend AS core-devel
ARG ROS_DISTRO
ARG ROS_PACKAGES_PROFILE

USER ${USERNAME}
WORKDIR /home/${USERNAME}

RUN --mount=type=bind,from=ansible,source=/opt/uv,target=/opt/uv \
    --mount=type=bind,source=ansible-galaxy-requirements.yaml,target=/tmp/ansible/ansible-galaxy-requirements.yaml \
    --mount=type=bind,source=ansible,target=/tmp/ansible/ansible \
    --mount=type=cache,id=apt-cache-${ROS_DISTRO},target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lists-${ROS_DISTRO},target=/var/lib/apt/lists,sharing=locked \
    export PATH="/opt/uv/bin:${PATH}" && \
    cd /tmp/ansible && \
    ansible-galaxy collection install -f -r ansible-galaxy-requirements.yaml && \
    ansible-playbook clover2.dev.install_deps \
    --tags simulation \
    --skip-tags core \
    -i /tmp/ansible/ansible/inventory.ini \
    -e rosdistro=${ROS_DISTRO} -e ros_packages_profile=${ROS_PACKAGES_PROFILE}

USER root

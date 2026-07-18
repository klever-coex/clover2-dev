ARG BASE_IMAGE=clover2-base

FROM ${BASE_IMAGE} AS core-depend
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG ROS_DISTRO

USER ${USERNAME}
WORKDIR /home/${USERNAME}

RUN rosdep update --rosdistro=${ROS_DISTRO} -r

RUN --mount=type=bind,source=ansible-galaxy-requirements.yaml,target=/tmp/ansible/ansible-galaxy-requirements.yaml \
    --mount=type=bind,source=ansible,target=/tmp/ansible/ansible \
    --mount=type=cache,id=apt-cache-${ROS_DISTRO},target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lists-${ROS_DISTRO},target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,id=pipx-cache,target=/home/dev/.cache/pipx,uid=1000,gid=1000 \
    pipx install --include-deps "ansible==10.*" && \
    cd /tmp/ansible && \
    ansible-galaxy collection install -f -r ansible-galaxy-requirements.yaml && \
    ansible-playbook clover2.dev.install_deps --tags core -i /tmp/ansible/ansible/inventory.ini \
    -e rosdistro=${ROS_DISTRO} && \
    pipx uninstall ansible

COPY --parents --chown=${USERNAME}:${USERNAME} src/**/package.xml /tmp/clover2-dev

USER root

RUN --mount=type=cache,id=apt-cache-${ROS_DISTRO},target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lists-${ROS_DISTRO},target=/var/lib/apt/lists,sharing=locked \
    apt-get update && \
    . "/opt/ros/${ROS_DISTRO}/setup.sh" && \
    rosdep install -y --from-paths /tmp/clover2-dev/src \
    --ignore-src \
    --rosdistro "${ROS_DISTRO}"

FROM core-depend AS core-devel
ARG ROS_DISTRO

USER ${USERNAME}
WORKDIR /home/${USERNAME}

RUN --mount=type=bind,source=ansible-galaxy-requirements.yaml,target=/tmp/ansible/ansible-galaxy-requirements.yaml \
    --mount=type=bind,source=ansible,target=/tmp/ansible/ansible \
    --mount=type=cache,id=apt-cache-${ROS_DISTRO},target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lists-${ROS_DISTRO},target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,id=pipx-cache,target=/home/dev/.cache/pipx,uid=1000,gid=1000 \
    pipx install --include-deps "ansible==10.*" && \
    cd /tmp/ansible && \
    ansible-galaxy collection install -f -r ansible-galaxy-requirements.yaml && \
    ansible-playbook clover2.dev.install_deps \
    --tags simulation \
    --skip-tags core \
    -i /tmp/ansible/ansible/inventory.ini \
    -e rosdistro=${ROS_DISTRO} && \
    pipx uninstall ansible

USER root
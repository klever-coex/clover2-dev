# check=skip=InvalidDefaultArgInFrom
ARG ROS_DISTRO

FROM ros:${ROS_DISTRO}-ros-base AS base
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG ROS_DISTRO
ARG USERNAME=dev

RUN --mount=type=cache,id=apt-cache-${ROS_DISTRO},target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lists-${ROS_DISTRO},target=/var/lib/apt/lists,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    sudo \
    bash-completion \
    iproute2 \
    pipx \
    gosu

RUN userdel -r ubuntu 2>/dev/null || true && \
    useradd -m -s /bin/bash -U ${USERNAME} && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/90-user-nopasswd && \
    chmod 0440 /etc/sudoers.d/90-user-nopasswd

ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

USER root
COPY --chmod=755 docker/entrypoint.sh /entrypoint.sh

ENV ROS_DISTRO=${ROS_DISTRO}
ENV USERNAME=${USERNAME}

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]

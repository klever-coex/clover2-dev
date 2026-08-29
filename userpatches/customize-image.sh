#!/bin/bash
#
# customize-image.sh — Clover2 image customization
#
# Executed inside chroot during Armbian image build.
# Installs ROS 2 Jazzy + MAVROS + dependencies via Ansible.
#
# Arguments: $RELEASE $LINUXFAMILY $BOARD $BUILD_DESKTOP

set -euo pipefail

RELEASE=$1
LINUXFAMILY=$2
BOARD=$3
BUILD_DESKTOP=$4

USER=pi
ROS_DISTRO=jazzy

# --- Pinned versions (reproducible builds) ---
ANSIBLE_VERSION="10.7.0"
CLOVER2_DEV_COMMIT="f4d9a02117a9a85e3a1cb3a3ec78d19f3049b25b"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
log_stage() { echo -e "${BLUE}[STAGE]${NC} $*"; }

install_ansible() {
    log_info "Installing Ansible ${ANSIBLE_VERSION} via pipx"

    apt-get install -y pipx make
    pipx install --include-deps "ansible==${ANSIBLE_VERSION}"

    log_info "Installing clover2-dev Ansible collection (commit ${CLOVER2_DEV_COMMIT})"
    /root/.local/bin/ansible-galaxy collection install \
        "git+https://github.com/klever-coex/clover2-dev.git,${CLOVER2_DEV_COMMIT}"
}

install_ros2() {
    log_info "Installing ROS 2 ${ROS_DISTRO} via Ansible"
    /root/.local/bin/ansible-playbook -vv \
        clover2.dev.install_deps --tags core \
        -i /home/${USER}/inventory.ini \
        -e rosdistro=${ROS_DISTRO}
}

install_mavros() {
    log_info "Installing MAVROS + geographiclib via Ansible"
    /root/.local/bin/ansible-playbook -vv \
        clover2.dev.install_geographiclib --tags geographiclib \
        -i /home/${USER}/inventory.ini \
        -e rosdistro=${ROS_DISTRO}
    /root/.local/bin/ansible-playbook -vv \
        clover2.dev.install_mavros --tags mavros \
        -i /home/${USER}/inventory.ini \
        -e rosdistro=${ROS_DISTRO}
}

Main() {
    export DEBIAN_FRONTEND=noninteractive
    export APT_LISTCHANGES_FRONTEND=none
    export LANG=en_US.UTF-8
    export LC_ALL=en_US.UTF-8

    apt-get update -y

    # --- Create pi user ---
    if ! id ${USER} &>/dev/null; then
        useradd -m -s /bin/bash \
            -G sudo,adm,dialout,cdrom,plugdev,video,audio,netdev,render \
            ${USER}
        echo "${USER}:raspberry" | chpasswd
        log_info "Created user: ${USER}"
    fi

    # --- Copy overlay files to rootfs ---
    if [[ -d /tmp/overlay/home ]]; then
        cp -r /tmp/overlay/home/* /home/
        log_info "Overlay /home applied."
    fi

    # --- Install ROS 2 + dependencies via Ansible ---
    apt-get install -y git
    locale-gen en_US.UTF-8

    install_ansible
    install_ros2
    install_mavros

    # --- Cleanup build artifacts ---
    rm -f /home/${USER}/inventory.ini

    log_info "Customization complete."
}

Main

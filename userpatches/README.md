# clover2-image

Armbian userpatches for the Clover2 autonomous quadcopter onboard computer.

**Target:** Raspberry Pi 4B / 5B (arm64)
**Base:** Armbian (Ubuntu 24.04 Noble Numbat)
**ROS:** ROS 2 Jazzy Jalisco (via Ansible)
**Default user:** `pi` / `raspberry`

## Quick Start

```bash
# 1. Clone Armbian build framework
git clone https://github.com/armbian/build.git clover2-build
cd clover2-build

# 2. Add clover2-image as userpatches submodule
git submodule add https://github.com/coex/clover2-image.git userpatches

# 3. Build the image
./compile.sh clover2-rpi4b

# 4. Flash to SD card
dd if=output/images/Armbian-*.img of=/dev/sdX bs=4M status=progress
```

## How It Works

This repo follows the standard [Armbian userpatches pattern](https://github.armbian.com/documentation/827/Developer-Guide_User-Configurations/). Reference: [indiedroid-nova](https://github.com/lanefu/armbian-userpatches-example-indiedroid-nova).

```
armbian/build/                  # Official framework (cloned separately)
  userpatches/                  # ← THIS REPO as git submodule
    config-clover2-rpi4b.conf
    customize-image.sh
    overlay/
```

## Project Structure

```
clover2-image/                  # This repo = userpatches content
├── README.md
├── config-clover2-rpi4b.conf   # Board config (Raspberry Pi 4B)
├── config-clover2-rpi5b.conf   # Board config (Raspberry Pi 5B)
├── customize-image.sh          # Post-install script (runs in chroot)
├── firstboot.conf              # Skip interactive first-boot wizard
│
├── overlay/                    # Files copied to image rootfs
│   ├── home/pi/                # Pi user: .bashrc, inventory.ini (build-time)
│   └── assets/                 # Static assets (camera_info, motd)
│
├── custom-repo/                # Local APT repository (M2: ROS metapackage)
│   └── conf/distributions
│
└── packages/                   # Custom .deb package sources (M2)
    └── ros2-jazzy-custom/
```

## Build Process

`customize-image.sh` executes inside chroot:

1. Creates `pi` user with sudo, dialout, video, render groups
2. Copies overlay files to `/home/pi/`
3. Installs Ansible via pipx (pinned to specific version)
4. Installs `clover2.dev` Ansible collection (pinned to commit hash)
5. Runs playbooks: `install_deps` (ROS 2 core) → `install_geographiclib` → `install_mavros`
6. Cleans up build artifacts (inventory.ini)

## Pinned Versions

For reproducible builds, dependencies are pinned in `customize-image.sh`:

| Dependency | Pin |
|-----------|-----|
| Ansible | `==10.7.0` (exact) |
| clover2-dev collection | Commit `f4d9a02` |

Update these when the collection changes.

## Milestones

- **M1:** Bare image with user + ROS 2 Jazzy → boots on Raspberry Pi
- **M2:** ROS 2 Jazzy + Clover2 dependencies via custom APT metapackage

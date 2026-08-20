# clover2-dev

## Host requirements

Install the following tools on the host:

- [Docker Engine](https://docs.docker.com/engine/install/) with Docker Compose
- `xhost`, used to allow graphical applications from the container to connect to the host display
- One of:
  - [Visual Studio Code](https://code.visualstudio.com/download/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
  - [Dev Container CLI](https://github.com/devcontainers/cli)

Install `xhost` using the package manager for your distribution:

```bash
# Ubuntu / Debian
sudo apt install x11-xserver-utils

# Arch Linux / CachyOS
sudo pacman -S xorg-xhost
```

## Start the development container

### Using Visual Studio Code

1. Open the project in Visual Studio Code.
2. Press `Ctrl+Shift+P` and select `Dev Containers: Reopen in Container`.
3. Select `clover2-dev:universe-devel`, or `clover2-dev:universe-devel (NVIDIA)` if you have an NVIDIA GPU.

### Using the Dev Container CLI

Install the CLI using npm:

```bash
npm install -g @devcontainers/cli
```

Start the regular development container:

```bash
devcontainer up \
  --workspace-folder . \
  --config .devcontainer/universe-devel/devcontainer.json
```

For an NVIDIA GPU, use the NVIDIA configuration instead:

```bash
devcontainer up \
  --workspace-folder . \
  --config .devcontainer/universe-devel-nvidia/devcontainer.json
```

Open a shell in the running container using the same configuration path:

```bash
devcontainer exec \
  --workspace-folder . \
  --config .devcontainer/universe-devel/devcontainer.json \
  bash
```

## Set up dependencies

Inside the development container:

```bash
vcs import src --recursive < repos/simulation.yaml
```

## Build

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

## Run

```bash
source ./install/setup.bash
ros2 launch clover2_sim gz_simple.launch.py
```

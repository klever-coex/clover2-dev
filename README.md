# clover2-dev

## Quick start

1. Install [Docker](https://docs.docker.com/engine/install/).
2. Install [VSCode](https://code.visualstudio.com/download/).
3. Install [Dev Container Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers/).
4. Open project in `Dev Container`. Press `Ctrl+Shift+P` and enter `Reopen in Container`.
5. Select `clover2-dev:universe-devel` or `clover2-dev:universe-devel (NVIDIA)` if you have nvidia GPU

## Setup depends

Inside `Dev Container`
```bash
vcs import src --recursive < repos/simulation.yaml
```

## Build

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --cmake-args  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

## Run
```bash
source ./install/setup.bash
ros2 launch clover2_sim gz_simple.launch.py
```

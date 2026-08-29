# ~/.bashrc — pi user on Clover2 Armbian image

[ -z "$PS1" ] && return

# Aliases
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'

# ROS 2 Jazzy
source /opt/ros/jazzy/setup.bash

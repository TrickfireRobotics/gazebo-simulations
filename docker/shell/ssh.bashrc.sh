#!/usr/bin/env bash
# RC file for SSH sessions. Sets up the prompt and aliases.

[ -f "$HOME/.bashrc" ] && . "$HOME/.bashrc"

cd ~/gazebo-simulations 2>/dev/null || true
source /opt/ros/${ROS_DISTRO}/setup.bash 2>/dev/null

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/prompt.sh"
[ -f "$SCRIPT_DIR/sim.aliases.sh" ] && . "$SCRIPT_DIR/sim.aliases.sh"

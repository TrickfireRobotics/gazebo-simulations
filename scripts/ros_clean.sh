#!/bin/bash
set -e

# ------------------------------------------------------------------------------
# ros_clean.sh
# Deletes the files that ROS builds, to prevent unexplainable issues.
# NOTE: This script is also ran as the 'postCreateCommand' for this devcontainer
# ------------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_DIR="$PROJECT_DIR/robot-sim"

cd "$WORKSPACE_DIR" || exit 1
echo "Deleting ROS build files..."
(rm -r log/ build/ install/ 2>/dev/null && echo "Done!") || echo "Files already cleaned!"

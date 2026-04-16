#!/usr/bin/env bash
# RC file for SSH sessions for NVIDIA PCs. Sets up the prompt and aliases.

[ -f "$HOME/.bashrc" ] && . "$HOME/.bashrc"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/prompt.sh"
[ -f "$SCRIPT_DIR/bash_aliases" ] && . "$SCRIPT_DIR/bash_aliases"

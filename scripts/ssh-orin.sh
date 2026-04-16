#!/bin/bash

TERM=xterm-256color ssh -t trickfire@192.168.0.211 \
    "cd ~/gazebo-simulations && PROMPT_ENV=orin-host bash --rcfile ~/gazebo-simulations/.devcontainer/shell/prompt_rc.sh"


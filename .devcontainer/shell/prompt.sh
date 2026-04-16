#!/usr/bin/env bash
# --------------------------------------------------------------------------------------------
# prompt.sh
# --------------------------------------------------------------------------------------------
# Sets a unified PS1 prompt across all project shells.
# Source this file — do NOT execute it directly.
#
# The prompt label and color are driven by $PROMPT_ENV:
#
#   local-dev   (blue)    — devcontainer on the local machine  [set by launch.sh → launch.env]
#   orin-host   (amber)   — SSH shell on the Orin host         [set by or-ssh.sh]
#   orin-dev    (green)   — devcontainer on the Orin           [set by launch.sh → launch.env]
#   orin-sim    (magenta) — gazebo-sim container on the Orin   [set by .devcontainer/docker-compose.yml]
# --------------------------------------------------------------------------------------------

# --- Colors (256-color ANSI escape sequences, wrapped for PS1 safety) ---
_R='\[\e[0m\]'       # reset
_B='\[\e[1m\]'       # bold
_D='\[\e[2m\]'       # dim

case "${PROMPT_ENV:-}" in
    local-dev)
        _C='\[\e[38;5;39m\]'    # dodger blue
        _L='LOCAL-DEV'
        ;;
    orin-host)
        _C='\[\e[38;5;214m\]'   # amber / orange
        _L='ORIN-HOST'
        ;;
    orin-dev)
        _C='\[\e[38;5;82m\]'    # bright green
        _L='ORIN-DEV'
        ;;
    orin-sim)
        _C='\[\e[38;5;201m\]'   # magenta
        _L='ORIN-SIM'
        ;;
    *)
        _C='\[\e[37m\]'         # plain white fallback
        _L="$PROMPT_ENV"
        ;;
esac

# --- PS1 ---
# Line 1: [LABEL] user@host  ~/path
# Line 2: $
PS1="\n${_C}${_B}[${_L}]${_R} ${_B}\u${_R}${_D}@\h${_R}  \[\e[34m\]\w${_R}\n\$ "

# Set xterm window title to: [LABEL] user@host: path
case "$TERM" in
    xterm*|rxvt*)
        PS1="\[\e]0;[${_L}] \u@\h: \w\a\]${PS1}"
        ;;
esac

unset _R _B _D _C _L

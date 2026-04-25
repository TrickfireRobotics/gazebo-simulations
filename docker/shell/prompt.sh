#!/usr/bin/env bash
# --------------------------------------------------------------------------------------------
# prompt.sh
# --------------------------------------------------------------------------------------------
# Sets a unified PS1 prompt across all project shells.
# Source this file to use the prompt, and set $PROMPT_ENV to control the label and color.
#
# The prompt label and color are driven by $PROMPT_ENV:
#
#   local-dev    (blue)    - devcontainer on the local machine  [set by launch.sh → launch.env]
#   <name>-host  (orange)   - SSH shell on a remote host        [set by ssh-pc.sh]
#   <name>-dev   (green)   - devcontainer on a remote host      [set by launch.sh → launch.env]
#   <name>-sim   (magenta) - gazebo-sim container               [set by .devcontainer/docker-compose.yml]
# --------------------------------------------------------------------------------------------

# --- Colors (256-color ANSI escape sequences, wrapped for PS1 safety) ---
_R='\[\e[0m\]' # reset
_B='\[\e[1m\]' # bold
_D='\[\e[2m\]' # dim

case "${PROMPT_ENV:-}" in
local-dev)
	_C='\[\e[38;5;39m\]' # blue
	_L='LOCAL-DEV'
	;;
*-host)
	_C='\[\e[38;5;214m\]' # orange
	_L="${PROMPT_ENV^^}"
	;;
*-dev)
	_C='\[\e[38;5;82m\]' # green
	_L="${PROMPT_ENV^^}"
	;;
*-sim)
	_C='\[\e[38;5;201m\]' # magenta
	_L="${PROMPT_ENV^^}"
	;;
*)
	_C='\[\e[37m\]' # white fallback
	_L="${PROMPT_ENV^^}"
	;;
esac

# --- PS1 ---
# Line 1: [LABEL] user@host  ~/path
# Line 2: $
PS1="\n${_C}${_B}[${_L}]${_R} ${_B}\u${_R}${_D}@\h${_R}  \[\e[34m\]\w${_R}\n\$ "

# Set xterm window title to: [LABEL] user@host: path
case "$TERM" in
xterm* | rxvt*)
	PS1="\[\e]0;[${_L}] \u@\h: \w\a\]${PS1}"
	;;
esac

unset _R _B _D _C _L

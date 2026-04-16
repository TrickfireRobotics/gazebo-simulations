#!/usr/bin/env bash
# --------------------------------------------------------------------------------------------
# prompt_rc.sh
# --------------------------------------------------------------------------------------------
# Used as a bash --rcfile for SSH sessions (orin_ssh.sh).
#
# Loads the regular user ~/.bashrc for aliases/completions, then overlays
# the unified project prompt on top. PROMPT_ENV must already be exported
# by the caller before launching bash.
# --------------------------------------------------------------------------------------------

[ -f "$HOME/.bashrc" ] && . "$HOME/.bashrc"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/prompt.sh"

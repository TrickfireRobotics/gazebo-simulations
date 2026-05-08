# --------------------------------------------------------------------------------------------
# gz-sim.bash_aliases
# --------------------------------------------------------------------------------------------
# Bash aliases for this (gazebo-simulations) project. Are moved to $HOME of the trickfire
# user and sourced by the `.bashrc`
# --------------------------------------------------------------------------------------------

# Quick clear
alias c="clear"

# List topics (l for list)
alias rtl="ros2 topic list"
alias gtl="ign topic -l"

# Listen to topics (e for echo)
alias rte="ros2 topic echo "
alias gte="ign topic -e -t "

# Genbot
alias genbot="env \$(grep -v '^#' .github/genbot/onshape.env 2>/dev/null | xargs 2>/dev/null) PYTHONPATH=.github python3 -m genbot"

# sim
alias sim="/home/trickfire/.local/bin/sim"

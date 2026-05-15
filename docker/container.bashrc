# Only run the interactive extras for interactive shells
case "$-" in
*i*) ;;
*) return ;;
esac

case ":$PATH:" in
*":$HOME/.local/bin:"*) ;;
*) export PATH="$HOME/.local/bin:$PATH" ;;
esac

# ---------- shell behavior ----------
export HISTCONTROL=ignoreboth:erasedups
export HISTSIZE=10000
export HISTFILESIZE=20000
shopt -s histappend checkwinsize

# ---------- locate repo/workspace ----------
_tf_find_repo() {
	local d
	for d in \
		"$PWD" \
		"$HOME/gazebo-simulations" \
		"/workspaces/gazebo-simulations" \
		"/workspace/gazebo-simulations"; do
		if [ -d "$d/robot-sim" ] && [ -f "$d/pyproject.toml" ]; then
			printf "%s\n" "$d"
			return 0
		fi
	done

	d="$(git rev-parse --show-toplevel 2>/dev/null || true)"
	if [ -n "$d" ] && [ -d "$d/robot-sim" ] && [ -f "$d/pyproject.toml" ]; then
		printf "%s\n" "$d"
		return 0
	fi

	return 1
}

if TF_REPO_DIR="$(_tf_find_repo)"; then
	export TF_REPO_DIR
	export TF_ROBOT_WS="$TF_REPO_DIR/robot-sim"
fi

# ---------- venv ----------
if [ -f "${TF_REPO_DIR}/.venv/bin/activate" ]; then
	source "${TF_REPO_DIR}/.venv/bin/activate"
fi

# ---------- display ----------
if [[ -n "${DISPLAY:-}" && "${DISPLAY}" != :* ]]; then
	export DISPLAY=":${DISPLAY}"
fi

# ---------- ROS/Gazebo environment ----------
tf_source_env() {
	if [ -f /opt/ros/jazzy/setup.bash ]; then
		# shellcheck source=/dev/null
		source /opt/ros/jazzy/setup.bash
	fi

	if [ -n "${TF_ROBOT_WS:-}" ] && [ -f "$TF_ROBOT_WS/install/setup.bash" ]; then
		# shellcheck source=/dev/null
		source "$TF_ROBOT_WS/install/setup.bash"

		local _sim_worlds_share="$TF_ROBOT_WS/install/sim_worlds/share/sim_worlds"
		if [ -d "$_sim_worlds_share/worlds" ]; then
			export GZ_SIM_RESOURCE_PATH="${GZ_SIM_RESOURCE_PATH:+$GZ_SIM_RESOURCE_PATH:}$_sim_worlds_share"
		fi
	fi
}

# Source env once per shell session.
if [ -z "${TF_ENV_SOURCED:-}" ]; then
	tf_source_env
	export TF_ENV_SOURCED=1
fi

# ---------- prompt ----------
_tf_git_branch() {
	git symbolic-ref --quiet --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null
}

_tf_prompt() {
	local branch=""
	local reset="\[\e[0m\]"
	local pink="\[\e[38;2;233;60;171m\]"
	local green="\[\e[38;2;1;255;0m\]"
	local blue="\[\e[38;2;80;170;255m\]"

	branch="$(_tf_git_branch)"
	if [ -n "$branch" ]; then
		branch=" ${blue}(${branch})${reset}"
	fi

	PS1="${pink}\u${reset}:${green}\w${reset}${branch}\\$ "
}
PROMPT_COMMAND="_tf_prompt"

# ---------- navigation ----------
if [ "${TF_AUTO_CD_REPO:-1}" = "1" ] && [ -n "${TF_REPO_DIR:-}" ] && [ "$PWD" = "$HOME" ]; then
	cd "$TF_REPO_DIR" || true
fi

# ---------- aliases ----------
alias c='clear'
alias ll='ls -alF --color=auto'
alias la='ls -A --color=auto'
alias l='ls -CF --color=auto'
alias ..='cd ..'
alias ...='cd ../..'

alias rtl='ros2 topic list'
alias rte='ros2 topic echo'
alias gtl='gz topic -l'
alias gte='gz topic -e -t'

alias simup='sim docker'
alias simclean='sim clean'

alias rws='cd "$TF_ROBOT_WS"'
alias rs='tf_source_env'
alias rsource='tf_source_env'

# ---------- helper functions ----------
ros-clean() {
	if [ -z "${TF_ROBOT_WS:-}" ]; then
		echo "robot workspace not found"
		return 1
	fi
	rm -rf "$TF_ROBOT_WS/build" "$TF_ROBOT_WS/install" "$TF_ROBOT_WS/log"
}

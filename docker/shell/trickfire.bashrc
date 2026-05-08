# ~/.bashrc for the trickfire user in the gazebo-simulations container

# Not interactive → bail out
case $- in *i*) ;; *) return ;; esac

# History
HISTCONTROL=ignoreboth
shopt -s histappend
HISTSIZE=1000
HISTFILESIZE=2000

# Update LINES and COLUMNS after each command
shopt -s checkwinsize

# Color support for ls and grep
if [ -x /usr/bin/dircolors ]; then
    eval "$(dircolors -b ~/.dircolors 2>/dev/null || dircolors -b)"
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
fi

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# Project aliases (sim.aliases.sh installed as ~/.bash_aliases by Dockerfile)
[ -f ~/.bash_aliases ] && . ~/.bash_aliases

# Bash completion
if ! shopt -oq posix; then
    if [ -f /usr/share/bash-completion/bash_completion ]; then
        . /usr/share/bash-completion/bash_completion
    elif [ -f /etc/bash_completion ]; then
        . /etc/bash_completion
    fi
fi

source /opt/ros/"${ROS_DISTRO}"/setup.bash
source ~/gazebo-simulations/docker/shell/prompt.sh

export PATH="$HOME/.local/bin:$PATH"
pip3 install -e ~/gazebo-simulations --user --quiet 2>/dev/null || true

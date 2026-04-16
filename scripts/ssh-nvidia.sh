#!/bin/bash

# --------------------------------------------------------------------------------------------
# ssh-nvidia.sh
# --------------------------------------------------------------------------------------------
# Interactively picks an NVIDIA PC from a list, then SSHes into it with a
# labelled prompt showing the PC name.
#
# To add a PC, append an entry to NVIDIA_PCS in the format "name|ip".
# --------------------------------------------------------------------------------------------

NVIDIA_PCS=(
    "orin|192.168.0.211"
    "xavier|192.168.0.148"
)

PC_NAME=""
PC_IP=""

if [[ -n "${1:-}" ]]; then
    for entry in "${NVIDIA_PCS[@]}"; do
        IFS='|' read -r name ip <<< "$entry"
        if [[ "$name" == "$1" ]]; then
            PC_NAME="$name"
            PC_IP="$ip"
            break
        fi
    done
    if [[ -z "$PC_IP" ]]; then
        echo "Unknown PC: $1"
        echo "Known PCs: $(IFS=','; for e in "${NVIDIA_PCS[@]}"; do IFS='|' read -r n _ <<< "$e"; printf ' %s' "$n"; done)"
        exit 1
    fi
else
    echo "Select a PC to connect to:"
    for i in "${!NVIDIA_PCS[@]}"; do
        IFS='|' read -r name ip <<< "${NVIDIA_PCS[$i]}"
        printf "  %d) %s  (%s)\n" "$((i+1))" "$name" "$ip"
    done

    read -rp "Enter number: " choice
    index=$((choice - 1))

    if [[ $index -lt 0 || $index -ge ${#NVIDIA_PCS[@]} ]]; then
        echo "Invalid selection."
        exit 1
    fi

    IFS='|' read -r PC_NAME PC_IP <<< "${NVIDIA_PCS[$index]}"
fi


TERM=xterm-256color ssh -Y -t -o GSSAPIAuthentication=no trickfire@"$PC_IP" \
    "if [ -d ~/gazebo-simulations ]; then cd ~/gazebo-simulations && PROMPT_ENV=${PC_NAME}-host bash --rcfile ~/gazebo-simulations/docker/shell/ssh.bashrc.sh; else bash; fi"

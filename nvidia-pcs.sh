#!/usr/bin/env bash
# --------------------------------------------------------------------------------------------
# nvidia-pcs.sh
# Registry of NVIDIA PCs (Jetsons) reachable over the network.
# Sourced by scripts that need to resolve PC names to IPs.
# --------------------------------------------------------------------------------------------

declare -A NVIDIA_PCS=(
	[orin]="192.168.0.211"
	[xavier]="192.168.0.205"
)

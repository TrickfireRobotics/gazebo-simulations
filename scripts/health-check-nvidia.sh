#!/bin/bash

# --------------------------------------------------------------------------------------------
# health-check-nvidia.sh
# --------------------------------------------------------------------------------------------
# Runs a health check on all NVIDIA PCs (or a specific one) and reports power mode,
# CPU/GPU state, fan, thermals, network, and service status with colour-coded output.
#
# Usage:
#   ./health-check-nvidia.sh           # check all PCs
#   ./health-check-nvidia.sh xavier    # check a specific PC
# --------------------------------------------------------------------------------------------

NVIDIA_PCS=(
	"orin|192.168.0.211"
	"xavier|192.168.0.148"
)

# colours
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

ok() { printf "  ${GREEN}✔${RESET}  %-28s ${GREEN}%s${RESET}\n" "$1" "$2"; }
warn() { printf "  ${YELLOW}⚠${RESET}  %-28s ${YELLOW}%s${RESET}\n" "$1" "$2"; }
fail() { printf "  ${RED}✘${RESET}  %-28s ${RED}%s${RESET}\n" "$1" "$2"; }

check_pc() {
	local PC_NAME="$1"
	local PC_IP="$2"

	printf "\n${BOLD}${CYAN}------------------------------------------${RESET}\n"
	printf "${BOLD}${CYAN}  %s  (%s)${RESET}\n" "$PC_NAME" "$PC_IP"
	printf "${BOLD}${CYAN}------------------------------------------${RESET}\n"

	# --- Ping / reachability ---
	local ping_ms
	ping_ms=$(ping -c 3 -W 1 "$PC_IP" 2>/dev/null | tail -1 | awk -F'/' '{printf "%.1f", $5}')
	local ping_loss
	ping_loss=$(ping -c 3 -W 1 "$PC_IP" 2>/dev/null | grep -oE '[0-9]+% packet loss' | grep -oE '[0-9]+')

	if [[ -z "$ping_loss" || "$ping_loss" -eq 100 ]]; then
		fail "Reachability" "unreachable"
		printf "\n"
		return
	elif [[ "$ping_loss" -gt 0 ]]; then
		warn "Reachability" "${ping_loss}% packet loss  (${ping_ms}ms avg)"
	elif (($(echo "$ping_ms > 20" | bc -l))); then
		warn "Ping latency" "${ping_ms}ms  (high for local network)"
	else
		ok "Reachability" "${ping_ms}ms avg  0% loss"
	fi

	# --- Collect remote data ---
	local remote
	remote=$(sshpass -p 'trickfire' ssh \
		-o GSSAPIAuthentication=no \
		-o StrictHostKeyChecking=no \
		-o ConnectTimeout=10 \
		trickfire@"$PC_IP" '
        echo "POWER_MODE=$(echo trickfire | sudo -S nvpmodel -q 2>/dev/null | grep "NV Power Mode" | cut -d: -f2 | xargs)"
        echo "CPUS_ONLINE=$(cat /sys/devices/system/cpu/online)"
        echo "GPU_FREQ=$(cat /sys/class/devfreq/*/cur_freq 2>/dev/null | head -1)"
        echo "FAN_PROFILE=$(cat /sys/devices/platform/thermal_fan_est/fan_profile 2>/dev/null)"
        echo "FAN_PWM=$(cat /sys/class/hwmon/hwmon*/pwm1 2>/dev/null | head -1)"
        echo "WIFI_PM=$(iwconfig wlan0 2>/dev/null | grep -oP "Power Management:\K\S+")"
        echo "ETH_CARRIER=$(cat /sys/class/net/eth0/carrier 2>/dev/null)"
        echo "ACTIVE_IFACE=$(ip route get 8.8.8.8 2>/dev/null | grep -oP "dev \K\S+")"
        echo "SVC_JETSON=$(systemctl is-active jetson-clocks.service 2>/dev/null)"
        echo "SVC_WIFI=$(systemctl is-active wifi-disable-powersave.service 2>/dev/null)"
        paste /sys/devices/virtual/thermal/thermal_zone*/type \
              /sys/devices/virtual/thermal/thermal_zone*/temp 2>/dev/null \
              | awk "{printf \"THERM_%s=%s\n\", \$1, \$2}"
        ' 2>/dev/null)

	if [[ -z "$remote" ]]; then
		fail "SSH" "could not connect"
		printf "\n"
		return
	fi

	# parse remote values
	get() { echo "$remote" | grep "^$1=" | cut -d= -f2-; }

	local power_mode cpu_online gpu_freq fan_profile fan_pwm wifi_pm eth_carrier active_iface svc_jetson svc_wifi
	power_mode=$(get POWER_MODE)
	cpu_online=$(get CPUS_ONLINE)
	gpu_freq=$(get GPU_FREQ)
	fan_profile=$(get FAN_PROFILE)
	fan_pwm=$(get FAN_PWM)
	wifi_pm=$(get WIFI_PM)
	eth_carrier=$(get ETH_CARRIER)
	active_iface=$(get ACTIVE_IFACE)
	svc_jetson=$(get SVC_JETSON)
	svc_wifi=$(get SVC_WIFI)

	# --- Power mode ---
	if [[ "$power_mode" == "MAXN" ]]; then
		ok "Power mode" "$power_mode"
	else
		warn "Power mode" "${power_mode:-unknown}  (expected MAXN)"
	fi

	# --- CPUs ---
	if [[ "$cpu_online" == "0-7" ]]; then
		ok "CPUs online" "all 8  ($cpu_online)"
	else
		warn "CPUs online" "$cpu_online  (expected 0-7)"
	fi

	# --- GPU ---
	if [[ -n "$gpu_freq" ]]; then
		local gpu_mhz=$((gpu_freq / 1000000))
		if [[ $gpu_mhz -ge 1000 ]]; then
			ok "GPU frequency" "${gpu_mhz} MHz"
		else
			warn "GPU frequency" "${gpu_mhz} MHz  (low)"
		fi
	else
		warn "GPU frequency" "unknown"
	fi

	# --- Fan ---

	if [[ "$fan_pwm" == "255" || "$fan_profile" == full* ]]; then
		ok "Fan profile" "full  (pwm=${fan_pwm:-?})"
	elif [[ "$fan_profile" == "quiet" || "$fan_profile" == "cool" ]]; then
		fail "Fan profile" "$fan_profile  (should be full, pwm=${fan_pwm:-?})"
	else
		warn "Fan profile" "${fan_profile:-unknown}  (pwm=${fan_pwm:-?})"
	fi

	# --- Thermals ---
	while IFS= read -r line; do
		[[ "$line" != THERM_* ]] && continue
		local zone temp_raw temp_c
		zone="${line#THERM_}"
		zone="${zone%%=*}"
		temp_raw="${line#*=}"
		temp_c=$((temp_raw / 1000))
		if [[ $temp_c -ge 80 ]]; then
			fail "Temp: $zone" "${temp_c}°C  (critical)"
		elif [[ $temp_c -ge 65 ]]; then
			warn "Temp: $zone" "${temp_c}°C  (warm)"
		fi
	done <<<"$remote"

	# --- Network ---
	if [[ "$eth_carrier" == "1" ]]; then
		ok "Ethernet" "connected"
	else
		warn "Ethernet" "no carrier  (using ${active_iface:-unknown})"
	fi

	if [[ "$wifi_pm" == "off" ]]; then
		ok "WiFi power management" "off"
	else
		warn "WiFi power management" "${wifi_pm:-unknown}  (should be off)"
	fi

	# --- Services ---
	if [[ "$svc_jetson" == "active" ]]; then
		ok "jetson-clocks.service" "active"
	else
		fail "jetson-clocks.service" "${svc_jetson:-inactive}"
	fi

	if [[ "$svc_wifi" == "active" ]]; then
		ok "wifi-disable-powersave" "active"
	else
		fail "wifi-disable-powersave" "${svc_wifi:-inactive}"
	fi

	printf "\n"
}

# --- Main ---
if [[ -n "${1:-}" ]]; then
	found=0
	for entry in "${NVIDIA_PCS[@]}"; do
		IFS='|' read -r name ip <<<"$entry"
		if [[ "$name" == "$1" ]]; then
			check_pc "$name" "$ip"
			found=1
			break
		fi
	done
	if [[ $found -eq 0 ]]; then
		echo "Unknown PC: $1"
		echo "Known PCs:$(for e in "${NVIDIA_PCS[@]}"; do
			IFS='|' read -r n _ <<<"$e"
			printf ' %s' "$n"
		done)"
		exit 1
	fi
else
	for entry in "${NVIDIA_PCS[@]}"; do
		IFS='|' read -r name ip <<<"$entry"
		check_pc "$name" "$ip"
	done
fi

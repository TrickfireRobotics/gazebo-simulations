#!/bin/bash
set -e

# --------------------------------------------------------------------------------------------
# Fetch raw OnShape URDF & assets into '.github/genbot/tests/' for local testing.
# Makes one API call per robot; afterwards use 'genbot local' with no API calls.
#
# Usage: ./genbot_tests.sh [robot_name [onshape_url]] [--output-dir <dir>]
#
# Examples:
#   ./genbot_tests.sh                      # fetch all robots from robots.json
#   ./genbot_tests.sh arm                  # fetch 'arm' from robots.json
#   ./genbot_tests.sh arm <onshape_url>    # fetch using a URL directly (not saved to registry)
#   ./genbot_tests.sh arm --output-dir /tmp/fixtures
# --------------------------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
GENBOT="$PROJECT_DIR/.github/genbot/genbot.py"
ROBOTS_JSON="$PROJECT_DIR/robots.json"

ROBOT_NAME=""
ONSHAPE_URL=""
OUTPUT_DIR_ARG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output-dir) OUTPUT_DIR_ARG="--output-dir $2"; shift 2 ;;
        --help)
            echo "Usage: $0 [robot_name [onshape_url]] [--output-dir <dir>]"
            echo ""
            echo "  robot_name    Robot to fetch. Omit to fetch all robots in robots.json."
            echo "  onshape_url   OnShape URL (optional — falls back to robots.json if omitted)."
            echo "  --output-dir  Where to save fixtures (default: .github/genbot/tests/)"
            exit 0
            ;;
        -*) echo "[Error] Unknown option: $1"; exit 1 ;;
        https://*) ONSHAPE_URL="$1"; shift ;;
        *)  ROBOT_NAME="$1"; shift ;;
    esac
done

if [ -z "$ONSHAPE_API_KEY" ] || [ -z "$ONSHAPE_API_SECRET" ]; then
    echo "[Error] ONSHAPE_API_KEY and ONSHAPE_API_SECRET must be set."
    exit 1
fi

if [ -n "$ROBOT_NAME" ]; then
    ROBOTS=("$ROBOT_NAME")
else
    if [ ! -f "$ROBOTS_JSON" ]; then
        echo "[Error] robots.json not found at $ROBOTS_JSON"
        exit 1
    fi
    mapfile -t ROBOTS < <(python3 -c "
import json
data = json.load(open('$ROBOTS_JSON'))
for r in data: print(r['name'])
")
    if [ ${#ROBOTS[@]} -eq 0 ]; then
        echo "[Error] No robots found in robots.json"
        exit 1
    fi
    echo "[Info] No robot specified — fetching all: ${ROBOTS[*]}"
fi

for robot in "${ROBOTS[@]}"; do
    echo ""
    echo "------------------------------------------------------"
    echo "Fetching: $robot"
    echo "------------------------------------------------------"
    # shellcheck disable=SC2086
    python3 "$GENBOT" raw "$robot" $ONSHAPE_URL $OUTPUT_DIR_ARG
done

echo ""
echo "[Done] Use genbot local to generate packages without further API calls:"
echo "  python3 .github/genbot/genbot.py local <robot> .github/genbot/tests/<robot>/robot.urdf"

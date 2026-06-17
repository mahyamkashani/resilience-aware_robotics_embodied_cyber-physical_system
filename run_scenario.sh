#!/bin/bash
#
# In this run file: we launch Webots + the IDS/resilience framework, inject an
# attack after a delay, and record the experiment result CSV.
#
# Usage:
#   ./run_scenario.sh [config] [attack] [result]
#
# Examples:
#   ./run_scenario.sh                                          # defaults below
#   ./run_scenario.sh configs/experiment2.json "left_arm:STOP" # non-resilient run
#   DELAY=8 DELAY2=15 ./run_scenario.sh configs/experiment4.json "left_wheels:STOP,right_wheels:STOP"
#
set -u

cd "$(dirname "$0")"

DELAY="${DELAY:-10}"     # seconds to let Webots load before starting the controller
DELAY2="${DELAY2:-20}"   # seconds after launch before injecting the attack

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment2.json}"
ATTACK="${2:-left_gripper:GRIP_WEAK}"
RESULT="${3:-../results/framework_correctness/exp1.csv}"

# Build the AttackState YAML from a comma-separated list of "device:type" entries.
IFS=',' read -ra _devs <<< "$ATTACK"
_devices_yaml=$(printf "'%s'," "${_devs[@]}")
_devices_yaml="[${_devices_yaml%,}]"

# --- clean slate: kill any running Webots ------------------------------------
clear
pkill -9 webots 2>/dev/null
sleep 2

# --- 1) launch Webots in the background --------------------------------------
echo "Launching Webots: $WORLD"
webots "$WORLD" &
WEBOTS_PID=$!

# --- 2) after a delay, start the controller / IDS framework ------------------
( sleep "$DELAY"; python3 "$CONTROLLER" "$CONFIG" "$RESULT" ) &
SIM_PID=$!

# --- 3) after a further delay, inject the attack -----------------------------
( sleep "$DELAY2"
  echo "Injecting attack: $_devices_yaml"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_devices_yaml}" ) &

# --- wait for the experiment to finish, then shut Webots down ----------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

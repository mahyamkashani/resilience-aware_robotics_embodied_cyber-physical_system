#!/bin/bash
#
# Usage:
#   ./data_phi_function.sh [config] [attack1] [result]
#
# Examples:
#   ./data_phi_function.sh                                           # defaults
#   ./data_phi_function.sh configs/experiment2.json "left_arm:STOP" # non-resilient run
#   DELAY=8 DELAY2=15 ./data_phi_function.sh configs/experiment4.json "left_wheels:STOP"
#   ATTACK2="right_arm:STOP" DELAY3=30 ./data_phi_function.sh
#
set -u

#cd "$(dirname "$0")"
cd "$(dirname "$0")/.."

DELAY="${DELAY:-5}"     # seconds to let Webots load before starting the controller, 5
DELAY2="${DELAY2:-10}"   # seconds after launch before injecting attack1, 15
DELAY3="${DELAY3:-15}"   # seconds after launch before injecting attack2, 30
DELAY4="${DELAY4:-20}"   # seconds after launch before injecting attack3, 50
DELAY5="${DELAY5:-25}"   # seconds after launch before injecting attack4, 75
DELAY6="${DELAY6:-28}"   # seconds after launch before injecting attack5, 102

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment4.json}"
ATTACK="${2:-left_gripper:GRIP_WEAK}"
ATTACK2="${3:-left_wheels:STOP}"
ATTACK3="${4:-right_wheels:UNDERSPEED}"
ATTACK4="${5:-left_arm:STOP}"
ATTACK5="${6:-right_arm:STOP}"

RESULT="${2:-../results/framework_correctness/exp4.csv}"

# attackState: comma-separated "device:type"
_make_yaml() {
  local attack="$1"
  local devs yaml
  IFS=',' read -ra devs <<< "$attack"
  yaml=$(printf "'%s'," "${devs[@]}")
  echo "[${yaml%,}]"
}

_yaml1=$(_make_yaml "$ATTACK")
_yaml2=$(_make_yaml "$ATTACK2")
_yaml3=$(_make_yaml "$ATTACK3")
_yaml4=$(_make_yaml "$ATTACK4")
_yaml5=$(_make_yaml "$ATTACK5")

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

# --- 3) inject each attack at its scheduled time -----------------------------
( sleep "$DELAY2"
  echo "Injecting attack1: $_yaml1"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" > /dev/null 2>&1 ) &

( sleep "$DELAY3"
  echo "Injecting attack2: $_yaml2"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" > /dev/null 2>&1 ) &

( sleep "$DELAY4"
  echo "Injecting attack3: $_yaml3"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml3}" > /dev/null 2>&1 ) &

( sleep "$DELAY5"
  echo "Injecting attack4: $_yaml4"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml4}" > /dev/null 2>&1 ) &

( sleep "$DELAY6"
  echo "Injecting attack5: $_yaml5"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml5}" > /dev/null 2>&1 ) &

wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

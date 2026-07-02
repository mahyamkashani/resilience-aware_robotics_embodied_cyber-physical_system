#!/bin/bash
#
# data_exp5.sh — five sequential attack waves designed to produce multiple
# NOT RESILIENT cycles when run with experiment5.json.
#
# Each wave attacks a tau=2 (critical) device, which triggers:
#   1. detection_delay_steps=50  (~1.6 s)  — psi drops, delta=0, NOT RESILIENT
#   2. mitigation_delay_steps=150 (~4.8 s) — mitigation activates, device cleared
#   3. System returns RESILIENT, ready for the next wave
#
# Wave gap is set to 10 s wall-clock to cover the full ~6.4 s cycle + buffer.
# If your Webots simulation runs slower than real-time, increase the DELAYs.
#
# Usage:
#   ./data_exp5.sh                         # all defaults
#   ./data_exp5.sh configs/experiment5.json ../results/framework_correctness/exp5.csv
#   DELAY2=15 WAVE1="right_wheels:STOP" ./data_exp5.sh
#
set -u

cd "$(dirname "$0")"

# Wall-clock delays from script launch
DELAY="${DELAY:-5}"     # time for Webots to load before starting the controller
DELAY2="${DELAY2:-10}"  # Wave 1 injection
DELAY3="${DELAY3:-20}"  # Wave 2 (10 s gap: > 1.6 s detection + 4.8 s mitigation)
DELAY4="${DELAY4:-30}"  # Wave 3
DELAY5="${DELAY5:-40}"  # Wave 4
DELAY6="${DELAY6:-50}"  # Wave 5 — escalation (both wheels)

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment5.json}"
RESULT="${2:-../results/framework_correctness/exp5.csv}"

# Each wave targets a tau=2 critical device so delta=0 fires immediately.
# Comma-separate multiple devices for a simultaneous multi-device wave.
WAVE1="${WAVE1:-left_wheels:STOP}"
WAVE2="${WAVE2:-right_wheels:STOP}"
WAVE3="${WAVE3:-left_wheels:UNDERSPEED}"
WAVE4="${WAVE4:-right_wheels:UNDERSPEED}"
WAVE5="${WAVE5:-left_wheels:STOP,right_wheels:STOP}"  # dual-device escalation

# Build an AttackState YAML list from a comma-separated "device:type" string.
_make_yaml() {
  local attack="$1"
  local devs yaml
  IFS=',' read -ra devs <<< "$attack"
  yaml=$(printf "'%s'," "${devs[@]}")
  echo "[${yaml%,}]"
}

_yaml1=$(_make_yaml "$WAVE1")
_yaml2=$(_make_yaml "$WAVE2")
_yaml3=$(_make_yaml "$WAVE3")
_yaml4=$(_make_yaml "$WAVE4")
_yaml5=$(_make_yaml "$WAVE5")

# --- clean slate: kill any running Webots ------------------------------------
clear
pkill -9 webots 2>/dev/null
sleep 2

# --- 1) launch Webots in the background --------------------------------------
echo "Launching Webots: $WORLD"
webots "$WORLD" &
WEBOTS_PID=$!

# --- 2) start the controller after load delay --------------------------------
( sleep "$DELAY"; python3 "$CONTROLLER" "$CONFIG" "$RESULT" ) &
SIM_PID=$!

# --- 3) inject attack waves --------------------------------------------------
( sleep "$DELAY2"
  echo "[Wave 1 @ ${DELAY2}s wall-clock]  $_yaml1"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" > /dev/null 2>&1 ) &

( sleep "$DELAY3"
  echo "[Wave 2 @ ${DELAY3}s wall-clock]  $_yaml2"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" > /dev/null 2>&1 ) &

( sleep "$DELAY4"
  echo "[Wave 3 @ ${DELAY4}s wall-clock]  $_yaml3"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml3}" > /dev/null 2>&1 ) &

( sleep "$DELAY5"
  echo "[Wave 4 @ ${DELAY5}s wall-clock]  $_yaml4"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml4}" > /dev/null 2>&1 ) &

( sleep "$DELAY6"
  echo "[Wave 5 @ ${DELAY6}s wall-clock]  $_yaml5"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml5}" > /dev/null 2>&1 ) &

# --- wait for the experiment to finish, then shut Webots down ----------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

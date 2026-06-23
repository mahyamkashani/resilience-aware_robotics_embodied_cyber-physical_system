#!/bin/bash
#
# data_exp6.sh — five sequential attack waves for experiment6.json.
#
# Uses alpha_crit=0.4, so any single tau=2 attack drops
# psi = 1 - 0.4 = 0.6 < theta_base=0.75 (not-tolerable / red band).
# Wave 5 hits two critical devices simultaneously: psi = 0.2.
#
# Each wave cycle:
#   detection_delay_steps=50  (~1.6 s) — device enters S, psi drops, NOT RESILIENT
#   mitigation_delay_steps=150 (~4.8 s) — mitigation activates, device cleared
#   Total cycle ~6.4 s; wave gap set to 10 s for safety.
#
# Outputs (written automatically by manual_run.py):
#   exp6.csv     — one summary row per run
#   exp6_psi.csv — psi sampled at 100 Hz throughout the simulation
#
# Usage:
#   ./data_exp6.sh                          # all defaults
#   ./data_exp6.sh configs/experiment6.json ../results/framework_correctness/exp6.csv
#   DELAY3=25 WAVE2="left_arm:STOP" ./data_exp6.sh
#
set -u

cd "$(dirname "$0")"

DELAY="${DELAY:-5}"     # Webots load time
DELAY2="${DELAY2:-10}"  # Wave 1
DELAY3="${DELAY3:-20}"  # Wave 2
DELAY4="${DELAY4:-30}"  # Wave 3
DELAY5="${DELAY5:-40}"  # Wave 4
DELAY6="${DELAY6:-50}"  # Wave 5 — dual-device escalation

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment6.json}"
RESULT="${2:-../results/framework_correctness/exp6.csv}"
# exp6_psi.csv is written alongside exp6.csv automatically by manual_run.py

# All tau=2 critical devices for experiment6:
#   left_wheels, right_wheels, left_arm, left_gripper
WAVE1="${WAVE1:-left_wheels:STOP}"                          # psi = 0.6
WAVE2="${WAVE2:-left_gripper:GRIP_WEAK}"                    # psi = 0.6
WAVE3="${WAVE3:-left_arm:STOP}"                             # psi = 0.6
WAVE4="${WAVE4:-right_wheels:UNDERSPEED}"                   # psi = 0.6
WAVE5="${WAVE5:-left_wheels:STOP,left_gripper:GRIP_WEAK}"   # psi = 0.2

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

# --- 1) launch Webots --------------------------------------------------------
echo "Launching Webots: $WORLD"
webots "$WORLD" &
WEBOTS_PID=$!

# --- 2) start the controller after load delay --------------------------------
( sleep "$DELAY"; python3 "$CONTROLLER" "$CONFIG" "$RESULT" ) &
SIM_PID=$!

# --- 3) inject attack waves --------------------------------------------------
( sleep "$DELAY2"
  echo "[Wave 1 @ ${DELAY2}s]  $_yaml1  →  psi=0.6"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" ) &

( sleep "$DELAY3"
  echo "[Wave 2 @ ${DELAY3}s]  $_yaml2  →  psi=0.6"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" ) &

( sleep "$DELAY4"
  echo "[Wave 3 @ ${DELAY4}s]  $_yaml3  →  psi=0.6"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml3}" ) &

( sleep "$DELAY5"
  echo "[Wave 4 @ ${DELAY5}s]  $_yaml4  →  psi=0.6"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml4}" ) &

( sleep "$DELAY6"
  echo "[Wave 5 @ ${DELAY6}s]  $_yaml5  →  psi=0.2  (dual-device escalation)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml5}" ) &

# --- wait for the experiment to finish, then shut Webots down ----------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT and ${RESULT%.csv}_psi.csv"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

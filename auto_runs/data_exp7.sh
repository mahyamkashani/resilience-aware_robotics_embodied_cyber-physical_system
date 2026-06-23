#!/bin/bash
#
# exp7_data.sh — five sequential attack waves for experiment7.json.
#
# Uses exponential_degradation:
#   psi = exp(-alpha_crit * k_crit) * exp(-alpha_base * k_base)
#
# Each wave mixes critical (tau=2) and non-critical (tau=1) devices to
# exercise both exponential criteria simultaneously:
#
#   Wave  Devices                                  k_crit  k_base  psi
#   1     left_wheels (crit)                         1       0     e^(-0.40)       ≈ 0.670
#   2     left_gripper (crit) + right_arm (base)     1       1     e^(-0.45)       ≈ 0.638
#   3     left_arm (crit) + right_gripper (base)     1       1     e^(-0.45)       ≈ 0.638
#   4     right_wheels (crit) + right_arm (base)     1       1     e^(-0.45)       ≈ 0.638
#   5     left_wheels+left_gripper (crit)
#         + right_arm (base)                         2       1     e^(-0.85)       ≈ 0.427
#
# Compare exp6_psi.csv (linear) vs exp7_psi.csv (exponential) to see the
# difference in degradation shape across identical attack sequences.
#
# Outputs (written automatically by manual_run.py):
#   exp7.csv     — one summary row per run
#   exp7_psi.csv — psi sampled at 100 Hz throughout the simulation
#
# Usage:
#   ./exp7_data.sh                          # all defaults
#   ./exp7_data.sh configs/experiment7.json ../results/framework_correctness/exp7.csv
#   DELAY3=25 WAVE2="left_arm:STOP,right_gripper:GRIP_WEAK" ./exp7_data.sh
#
set -u

cd "$(dirname "$0")"

DELAY="${DELAY:-5}"     # Webots load time
DELAY2="${DELAY2:-10}"  # Wave 1
DELAY3="${DELAY3:-20}"  # Wave 2
DELAY4="${DELAY4:-30}"  # Wave 3
DELAY5="${DELAY5:-40}"  # Wave 4
DELAY6="${DELAY6:-50}"  # Wave 5 — dual-critical + non-critical escalation

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment7.json}"
RESULT="${2:-../results/framework_correctness/exp7.csv}"
# exp7_psi.csv is written alongside exp7.csv automatically by manual_run.py

# Critical (tau=2): left_wheels, right_wheels, left_arm, left_gripper
# Non-critical (tau=1): right_arm, right_gripper
WAVE1="${WAVE1:-left_wheels:STOP}"
WAVE2="${WAVE2:-left_gripper:GRIP_WEAK,right_arm:STOP}"
WAVE3="${WAVE3:-left_arm:STOP,right_gripper:GRIP_WEAK}"
WAVE4="${WAVE4:-right_wheels:UNDERSPEED,right_arm:STOP}"
WAVE5="${WAVE5:-left_wheels:STOP,left_gripper:GRIP_WEAK,right_arm:STOP}"

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
  echo "[Wave 1 @ ${DELAY2}s]  $_yaml1  →  psi≈0.670  (1 crit)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" ) &

( sleep "$DELAY3"
  echo "[Wave 2 @ ${DELAY3}s]  $_yaml2  →  psi≈0.638  (1 crit + 1 non-crit)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" ) &

( sleep "$DELAY4"
  echo "[Wave 3 @ ${DELAY4}s]  $_yaml3  →  psi≈0.638  (1 crit + 1 non-crit)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml3}" ) &

( sleep "$DELAY5"
  echo "[Wave 4 @ ${DELAY5}s]  $_yaml4  →  psi≈0.638  (1 crit + 1 non-crit)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml4}" ) &

( sleep "$DELAY6"
  echo "[Wave 5 @ ${DELAY6}s]  $_yaml5  →  psi≈0.427  (2 crit + 1 non-crit)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml5}" ) &

# --- wait for the experiment to finish, then shut Webots down ----------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT and ${RESULT%.csv}_psi.csv"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

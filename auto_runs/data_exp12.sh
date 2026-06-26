#!/bin/bash
#
# data_exp12.sh — four escalating waves for experiment12.json.
#
# Attacks only critical (tau=2) devices.
# alpha_crit=0.08 — psi gradually crosses theta_crit=0.8 on wave 3.
# No mitigation enabled → system cannot recover → task HALTED.
#
#   psi = exp(-alpha_crit × k_crit) × exp(-alpha_base × k_base)
#
#   Wave  Critical (tau=2) devices                             k_c  psi      region
#   1     left_wheels                                          1    ≈0.923   tolerable
#   2     left_wheels+left_arm                                 2    ≈0.852   tolerable
#   3     left_wheels+left_arm+left_gripper                    3    ≈0.787   NOT tolerable → gamma=0
#   4     left_wheels+left_arm+left_gripper+right_arm          4    ≈0.726   NOT tolerable
# After wave 3 psi drops below theta_crit=0.8 → gamma=0 → NOT RESILIENT.
# No mitigation possible → HALTED at 2×baseline_time = 97.6 s.
#
# Outputs (written automatically by manual_run.py):
#   exp12.csv       — summary row
#   exp12_psi.csv   — psi sampled at 100 Hz
#   exp12_delta.csv — delta sampled at 100 Hz
#
# Usage:
#   ./data_exp12.sh
#   ./data_exp12.sh configs/experiment12.json ../results/framework_correctness/exp12.csv
#
set -u

#cd "$(dirname "$0")"
cd "$(dirname "$0")/.."

DELAY="${DELAY:-5}"     # Webots load time
DELAY2="${DELAY2:-8}"   # Wave 1: first critical device
DELAY3="${DELAY3:-20}"  # Wave 2: second critical device added
DELAY4="${DELAY4:-25}"  # Wave 3: third critical device added → psi crosses theta_crit=0.8
DELAY5="${DELAY5:-32}"  # Wave 4: fourth critical device (right_arm) added → psi drops further

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment12.json}"
RESULT="${2:-../results/framework_correctness/exp12.csv}"

WAVE1="${WAVE1:-left_wheels:STOP}"
WAVE2="${WAVE2:-left_wheels:STOP, left_arm:STOP}"
WAVE3="${WAVE3:-left_wheels:STOP,left_arm:STOP,left_gripper:STOP}"
WAVE4="${WAVE4:-left_wheels:STOP,left_arm:STOP,left_gripper:STOP,right_arm:STOP}"

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

# --- 3) inject escalating attack waves ---------------------------------------
( sleep "$DELAY2"
  echo "[Wave 1 @ ${DELAY2}s]  $_yaml1"
  echo "  k_crit=1, k_base=0 → psi≈0.923  (above theta_crit=0.80, tolerable)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" > /dev/null 2>&1 ) &

( sleep "$DELAY3"
  echo "[Wave 2 @ ${DELAY3}s]  $_yaml2"
  echo "  k_crit=2, k_base=0 → psi≈0.852  (above theta_crit=0.80, tolerable)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" > /dev/null 2>&1 ) &

( sleep "$DELAY4"
  echo "[Wave 3 @ ${DELAY4}s]  $_yaml3"
  echo "  k_crit=3, k_base=0 → psi≈0.787  (BELOW theta_crit=0.80 → gamma=0)"
  echo "  No mitigation available → system will HALT at 2×baseline (97.6 s)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml3}" > /dev/null 2>&1 ) &

( sleep "$DELAY5"
  echo "[Wave 4 @ ${DELAY5}s]  $_yaml4"
  echo "  k_crit=4, k_base=0 → psi≈0.726  (BELOW theta_crit=0.80 → gamma=0)"
  echo "  No mitigation available → system will HALT at 2×baseline (97.6 s)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml4}" > /dev/null 2>&1 ) &

# --- wait for the experiment to finish, then shut Webots down ----------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"
echo "  psi timeline  : ${RESULT%.csv}_psi.csv"
echo "  delta timeline: ${RESULT%.csv}_delta.csv"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

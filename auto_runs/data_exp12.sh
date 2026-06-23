#!/bin/bash
#
# data_exp12.sh — three escalating mixed-device waves for experiment12.json.
#
# Attacks both critical (tau=2) and non-critical (tau=1) devices.
# alpha_crit=0.08, alpha_base=0.04 — psi gradually crosses theta_crit=0.8 on wave 3.
# No mitigation enabled → system cannot recover → task HALTED.
#
#   psi = exp(-alpha_crit × k_crit) × exp(-alpha_base × k_base)
#
#   Wave  Critical (tau=2)       Non-crit (tau=1)  k_c  k_b  psi      region
#   1     left_wheels            right_arm          1    1    ≈0.887   tolerable
#   2     left_wheels+left_arm   right_arm          2    1    ≈0.819   tolerable
#   3     left_wheels+left_arm   right_arm          2    2    ≈0.787   NOT tolerable
#                                + right_gripper                       → gamma=0
#
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

cd "$(dirname "$0")"

DELAY="${DELAY:-5}"     # Webots load time
DELAY2="${DELAY2:-8}"   # Wave 1: first critical + non-critical
DELAY3="${DELAY3:-25}"  # Wave 2: second critical added
DELAY4="${DELAY4:-45}"  # Wave 3: second non-critical added → psi crosses threshold

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment12.json}"
RESULT="${2:-../results/framework_correctness/exp12.csv}"

WAVE1="${WAVE1:-left_wheels:STOP,right_arm:STOP}"
WAVE2="${WAVE2:-left_wheels:STOP,left_arm:STOP,right_arm:STOP}"
WAVE3="${WAVE3:-left_wheels:STOP,left_arm:STOP,right_arm:STOP,right_gripper:GRIP_WEAK}"

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
  echo "  k_crit=1, k_base=1 → psi≈0.887  (above theta_crit=0.80, tolerable)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" ) &

( sleep "$DELAY3"
  echo "[Wave 2 @ ${DELAY3}s]  $_yaml2"
  echo "  k_crit=2, k_base=1 → psi≈0.819  (above theta_crit=0.80, tolerable)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" ) &

( sleep "$DELAY4"
  echo "[Wave 3 @ ${DELAY4}s]  $_yaml3"
  echo "  k_crit=2, k_base=2 → psi≈0.787  (BELOW theta_crit=0.80 → gamma=0)"
  echo "  No mitigation available → system will HALT at 2×baseline (97.6 s)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml3}" ) &

# --- wait for the experiment to finish, then shut Webots down ----------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"
echo "  psi timeline  : ${RESULT%.csv}_psi.csv"
echo "  delta timeline: ${RESULT%.csv}_delta.csv"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

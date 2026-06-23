#!/bin/bash
#
# data_exp11.sh — four mixed-device attack waves for experiment11.json.
#
# Attacks both critical (tau=2) and non-critical (tau=1) devices.
# alpha_crit=0.04, alpha_base=0.02 — psi stays above theta_crit=0.8 throughout.
# All devices are mitigatable → system recovers after each wave → task DONE.
#
# left_gripper is intentionally never attacked so the robot keeps holding the
# bottle during navigation.  right_gripper (tau=1, non-critical) is used instead
# where a gripper attack is needed, as it does not affect the working arm.
#
#   psi = exp(-alpha_crit × k_crit) × exp(-alpha_base × k_base)
#
#   Wave  Critical (tau=2)       Non-crit (tau=1)              k_c  k_b  psi
#   1     left_wheels            right_arm                      1    1    ≈0.942
#   2     left_wheels            right_arm                      2    1    ≈0.922
#         + left_arm
#   3     left_wheels            right_arm                      2    2    ≈0.887
#         + left_arm             + right_gripper:GRIP_WEAK
#   4     left_arm               right_wheels + right_arm       1    3    ≈0.904
#                                + right_gripper:GRIP_WEAK
#
# All waves remain above theta_crit=0.8 → gamma=1, system RESILIENT → task DONE.
#
# Outputs (written automatically by manual_run.py):
#   exp11.csv       — summary row
#   exp11_psi.csv   — psi sampled at 100 Hz
#   exp11_delta.csv — delta sampled at 100 Hz
#
# Usage:
#   ./data_exp11.sh
#   ./data_exp11.sh configs/experiment11.json ../results/framework_correctness/exp11.csv
#
set -u

cd "$(dirname "$0")"

DELAY="${DELAY:-5}"     # Webots load time
DELAY2="${DELAY2:-8}"   # Wave 1
DELAY3="${DELAY3:-20}"  # Wave 2
DELAY4="${DELAY4:-32}"  # Wave 3
DELAY5="${DELAY5:-44}"  # Wave 4

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment11.json}"
RESULT="${2:-../results/framework_correctness/exp11.csv}"

WAVE1="${WAVE1:-left_wheels:STOP,right_arm:STOP}"
WAVE2="${WAVE2:-left_wheels:STOP,left_arm:STOP,right_arm:STOP}"
WAVE3="${WAVE3:-left_wheels:STOP,left_arm:STOP,right_arm:STOP,right_gripper:GRIP_WEAK}"
WAVE4="${WAVE4:-left_arm:STOP,right_wheels:UNDERSPEED,right_arm:STOP,right_gripper:GRIP_WEAK}"

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

# --- 3) inject attack waves --------------------------------------------------
( sleep "$DELAY2"
  echo "[Wave 1 @ ${DELAY2}s]  $_yaml1"
  echo "  k_crit=1, k_base=1 → psi≈0.942  (above theta_crit=0.80)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" ) &

( sleep "$DELAY3"
  echo "[Wave 2 @ ${DELAY3}s]  $_yaml2"
  echo "  k_crit=2, k_base=1 → psi≈0.922  (above theta_crit=0.80)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" ) &

( sleep "$DELAY4"
  echo "[Wave 3 @ ${DELAY4}s]  $_yaml3"
  echo "  k_crit=2, k_base=2 → psi≈0.887  (above theta_crit=0.80)"
  echo "  right_gripper:GRIP_WEAK — working arm unaffected, bottle held"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml3}" ) &

( sleep "$DELAY5"
  echo "[Wave 4 @ ${DELAY5}s]  $_yaml4"
  echo "  k_crit=1, k_base=3 → psi≈0.904  (above theta_crit=0.80)"
  echo "  right_gripper:GRIP_WEAK — working arm unaffected, bottle held"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml4}" ) &

# --- wait for the experiment to finish, then shut Webots down ----------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"
echo "  psi timeline  : ${RESULT%.csv}_psi.csv"
echo "  delta timeline: ${RESULT%.csv}_delta.csv"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

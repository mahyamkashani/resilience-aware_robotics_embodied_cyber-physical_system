#!/bin/bash
#
# data_exp9.sh — four attack waves using experiment9.json.
#
# All devices are critical (tau=2). alpha_crit=0.05 is small enough that
# psi stays above theta_crit=0.8 even with up to 4 simultaneous devices in S.
#
#   Wave  Devices                            k_crit  psi = exp(-0.05×k)
#   1     left_wheels                          1      exp(-0.05) ≈ 0.951
#   2     left_wheels + right_wheels           2      exp(-0.10) ≈ 0.905
#   3     left_arm + right_arm                 2      exp(-0.10) ≈ 0.905
#   4     left_wheels + left_arm + left_gripper 3     exp(-0.15) ≈ 0.861
#
# All waves stay above theta_crit=0.8 → gamma=1 throughout → psi timeline
# remains in the green "Tolerable" band for every attack.
#
# Outputs (written automatically by manual_run.py):
#   exp9.csv       — summary row
#   exp9_psi.csv   — psi sampled at 100 Hz
#   exp9_delta.csv — delta sampled at 100 Hz
#
# Usage:
#   ./data_exp9.sh
#   ./data_exp9.sh configs/experiment9.json ../results/framework_correctness/exp9.csv
#
set -u

cd "$(dirname "$0")"

DELAY="${DELAY:-5}"     # Webots load time
DELAY2="${DELAY2:-8}"   # Wave 1
DELAY3="${DELAY3:-18}"  # Wave 2
DELAY4="${DELAY4:-28}"  # Wave 3
DELAY5="${DELAY5:-38}"  # Wave 4

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment9.json}"
RESULT="${2:-../results/framework_correctness/exp9.csv}"

WAVE1="${WAVE1:-left_wheels:STOP}"
WAVE2="${WAVE2:-left_wheels:STOP,right_wheels:UNDERSPEED}"
WAVE3="${WAVE3:-left_arm:STOP,right_arm:STOP}"
WAVE4="${WAVE4:-left_wheels:STOP,left_arm:STOP,left_gripper:GRIP_WEAK}"

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
  echo "[Wave 1 @ ${DELAY2}s]  $_yaml1  →  psi≈0.951  (k=1, above theta_crit=0.8)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" ) &

( sleep "$DELAY3"
  echo "[Wave 2 @ ${DELAY3}s]  $_yaml2  →  psi≈0.905  (k=2, above theta_crit=0.8)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" ) &

( sleep "$DELAY4"
  echo "[Wave 3 @ ${DELAY4}s]  $_yaml3  →  psi≈0.905  (k=2, above theta_crit=0.8)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml3}" ) &

( sleep "$DELAY5"
  echo "[Wave 4 @ ${DELAY5}s]  $_yaml4  →  psi≈0.861  (k=3, above theta_crit=0.8)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml4}" ) &

# --- wait for the experiment to finish, then shut Webots down ----------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"
echo "  psi timeline  : ${RESULT%.csv}_psi.csv"
echo "  delta timeline: ${RESULT%.csv}_delta.csv"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

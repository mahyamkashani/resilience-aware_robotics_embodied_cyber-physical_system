#!/bin/bash
#
# data_exp10.sh — three escalating attack waves for experiment10.json.
#
# All devices are critical (tau=2). No mitigation enabled → system cannot
# recover after any wave and eventually HALTs at 2 × baseline_time (97.6 s).
#
# Each wave REPLACES the previous attack list (cumulative device count grows):
#
#   Wave  Devices                        k_crit  psi = exp(-0.1×k)   region
#   1     left_wheels                      1      exp(-0.1) ≈ 0.905   tolerable
#   2     left_wheels + right_wheels       2      exp(-0.2) ≈ 0.819   tolerable
#   3     left_wheels + right_wheels       3      exp(-0.3) ≈ 0.741   NOT tolerable
#         + left_arm                                                   → gamma=0
#
# After wave 3 psi drops below theta_crit=0.8 → gamma=0.
# No mitigation is possible → system stays NOT RESILIENT → HALTED.
#
# Outputs (written automatically by manual_run.py):
#   exp10.csv       — summary row
#   exp10_psi.csv   — psi sampled at 100 Hz
#   exp10_delta.csv — delta sampled at 100 Hz
#
# Usage:
#   ./data_exp10.sh
#   ./data_exp10.sh configs/experiment10.json ../results/framework_correctness/exp10.csv
#
set -u

cd "$(dirname "$0")"

DELAY="${DELAY:-5}"     # Webots load time
DELAY2="${DELAY2:-8}"   # Wave 1: first critical device
DELAY3="${DELAY3:-20}"  # Wave 2: second critical device added
DELAY4="${DELAY4:-35}"  # Wave 3: third critical device — psi crosses theta_crit

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment10.json}"
RESULT="${2:-../results/framework_correctness/exp10.csv}"

WAVE1="${WAVE1:-left_wheels:STOP}"
WAVE2="${WAVE2:-left_wheels:STOP,right_wheels:UNDERSPEED}"
WAVE3="${WAVE3:-left_wheels:STOP,right_wheels:UNDERSPEED,left_arm:STOP}"

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
  echo "  k=1 → psi≈0.905  (above theta_crit=0.80, tolerable)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" > /dev/null 2>&1 ) &

( sleep "$DELAY3"
  echo "[Wave 2 @ ${DELAY3}s]  $_yaml2"
  echo "  k=2 → psi≈0.819  (above theta_crit=0.80, tolerable)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" > /dev/null 2>&1 ) &

( sleep "$DELAY4"
  echo "[Wave 3 @ ${DELAY4}s]  $_yaml3"
  echo "  k=3 → psi≈0.741  (BELOW theta_crit=0.80 → gamma=0, NOT tolerable)"
  echo "  No mitigation available → system will HALT at 2×baseline (97.6 s)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml3}" > /dev/null 2>&1 ) &

# --- wait for the experiment to finish, then shut Webots down ----------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"
echo "  psi timeline  : ${RESULT%.csv}_psi.csv"
echo "  delta timeline: ${RESULT%.csv}_delta.csv"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

#!/bin/bash
#
# data_exp16.sh — wheel-only attacks on navigate_to_goal (box2).
#
# Attacks 1 critical device (left_wheels, tau=1) and 1 non-critical device (right_wheels, tau=1).
# alpha_base=0.08, theta_base=0.72, baseline=20 s.
# No mitigation; psi stays above theta_base in both waves → tolerable degradation (delta=1, gamma=1).
#
#   psi = exp(-alpha_base × k_base)   (both devices tau=1, k_crit=0)
#
#   Wave  Devices (both tau=1)           k_b  psi      region
#   1     left_wheels  [critical]         1    ≈0.923   tolerable   (delta=1, gamma=1)
#   2     +right_wheels [non-critical]    2    ≈0.852   tolerable   (delta=1, gamma=1)

# Outputs (written by manual_run.py):
#   exp16.csv       — summary row (appended each run)
#   exp16_psi.csv   — psi sampled at 100 Hz
#   exp16_delta.csv — delta sampled at 100 Hz
#
# Usage:
#   ./auto_runs/data_exp16.sh
#   ./auto_runs/data_exp16.sh configs/experiment16.json ../results/framework_correctness/exp16.csv
#
set -u

cd "$(dirname "$0")/.."

DELAY="${DELAY:-10}"    # Webots load time
DELAY2="${DELAY2:-12}"  # Wave 1: left_wheels (tau=1, critical) — 2 s into task
DELAY3="${DELAY3:-17}"  # Wave 2: +right_wheels (tau=1, non-critical) — 7 s into task
#DELAY4="${DELAY4:-22}"  # Wave 3: both wheels — 12 s into task
#DELAY5="${DELAY5:-32}"  # Wave 4: both wheels again — sustained pressure

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment16.json}"
RESULT="${2:-../results/framework_correctness/exp16.csv}"

WAVE1="${WAVE1:-left_wheels:STOP}"
WAVE2="${WAVE2:-left_wheels:STOP,right_wheels:STOP}"
#WAVE3="${WAVE3:-left_wheels:STOP,right_wheels:STOP}"
#WAVE4="${WAVE4:-left_wheels:STOP,right_wheels:STOP}"

_make_yaml() {
  local attack="$1"
  local devs yaml
  IFS=',' read -ra devs <<< "$attack"
  yaml=$(printf "'%s'," "${devs[@]}")
  echo "[${yaml%,}]"
}

_yaml1=$(_make_yaml "$WAVE1")
_yaml2=$(_make_yaml "$WAVE2")
#_yaml3=$(_make_yaml "$WAVE3")
#_yaml4=$(_make_yaml "$WAVE4")

# --- clean slate -------------------------------------------------------------
clear
pkill -9 webots 2>/dev/null
sleep 2

# --- launch Webots -----------------------------------------------------------
echo "Launching Webots: $WORLD"
webots "$WORLD" &
WEBOTS_PID=$!

# --- start controller --------------------------------------------------------
( sleep "$DELAY"; python3 "$CONTROLLER" "$CONFIG" "$RESULT" ) &
SIM_PID=$!

# --- inject attacks ----------------------------------------------------------
( sleep "$DELAY2"
  echo "[Wave 1 @ ${DELAY2}s]  $_yaml1  k_base=1 → psi≈0.923  (tolerable, delta=1, gamma=1)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" > /dev/null 2>&1 ) &

( sleep "$DELAY3"
  echo "[Wave 2 @ ${DELAY3}s]  $_yaml2  k_base=2 → psi≈0.852  (tolerable, delta=1, gamma=1)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" > /dev/null 2>&1 ) &

# ( sleep "$DELAY4"
#   echo "[Wave 3 @ ${DELAY4}s]  $_yaml3  k_base=2 → psi≈0.852"
#   ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
#     "{compromised_devices: $_yaml3}" > /dev/null 2>&1 ) &

# ( sleep "$DELAY5"
#   echo "[Wave 4 @ ${DELAY5}s]  $_yaml4  sustained dual-wheel attack"
#   ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
#     "{compromised_devices: $_yaml4}" > /dev/null 2>&1 ) &

# --- wait and clean up -------------------------------------------------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"
echo "  psi timeline  : ${RESULT%.csv}_psi.csv"
echo "  delta timeline: ${RESULT%.csv}_delta.csv"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

#!/bin/bash
#
# data_exp19.sh — non-critical-only attacks on navigate_to_goal (box2), STAY RESILIENT.
#
# Attacks 2 non-critical devices (right_wheels tau=1, right_arm tau=1). k_crit=0.
# alpha_base=0.04, theta_base=0.72, baseline=20 s. No mitigation.
# Both waves keep psi well above theta_base → gamma=1 throughout → RESILIENT.
#
#   psi = exp(-alpha_base × k_base)   (k_crit=0, threshold = theta_base)
#
#   Wave  Devices (both tau=1)             k_b  psi      region
#   1     right_wheels  [non-critical]      1    ≈0.961   tolerable   (delta=1, gamma=1)
#   2     +right_arm    [non-critical]      2    ≈0.923   tolerable   (delta=1, gamma=1)
#
# Outputs (written by manual_run.py):
#   exp19.csv       — summary row (appended each run)
#   exp19_psi.csv   — psi sampled at 100 Hz
#   exp19_delta.csv — delta sampled at 100 Hz
#
# Usage:
#   ./auto_runs/data_exp19.sh
#   ./auto_runs/data_exp19.sh configs/experiment19.json ../results/framework_correctness/exp19.csv
#
set -u

cd "$(dirname "$0")/.."

DELAY="${DELAY:-10}"    # Webots load time
DELAY2="${DELAY2:-12}"  # Wave 1: right_wheels (tau=1, non-critical) — 2 s into task
DELAY3="${DELAY3:-17}"  # Wave 2: +right_arm (tau=1, non-critical) — 7 s into task

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment19.json}"
RESULT="${2:-../results/framework_correctness/exp19.csv}"

WAVE1="${WAVE1:-right_wheels:STOP}"
WAVE2="${WAVE2:-right_wheels:STOP,right_arm:STOP}"

_make_yaml() {
  local attack="$1"
  local devs yaml
  IFS=',' read -ra devs <<< "$attack"
  yaml=$(printf "'%s'," "${devs[@]}")
  echo "[${yaml%,}]"
}

_yaml1=$(_make_yaml "$WAVE1")
_yaml2=$(_make_yaml "$WAVE2")

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
  echo "[Wave 1 @ ${DELAY2}s]  $_yaml1  k_base=1 → psi≈0.961  (tolerable, delta=1, gamma=1)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" > /dev/null 2>&1 ) &

( sleep "$DELAY3"
  echo "[Wave 2 @ ${DELAY3}s]  $_yaml2  k_base=2 → psi≈0.923  (tolerable, delta=1, gamma=1)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" > /dev/null 2>&1 ) &

# --- wait and clean up -------------------------------------------------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"
echo "  psi timeline  : ${RESULT%.csv}_psi.csv"
echo "  delta timeline: ${RESULT%.csv}_delta.csv"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

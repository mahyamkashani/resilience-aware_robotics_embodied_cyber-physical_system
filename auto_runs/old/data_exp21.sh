#!/bin/bash
#
# data_exp21.sh — non-critical-only attacks on navigate_to_goal (box2), WITH mitigation.
#
# Attacks 2 non-critical devices (right_wheels tau=1, right_arm tau=1). k_crit=0.
# alpha_base=0.20, theta_base=0.72, baseline=20 s.
# Wave 2 crosses theta_base (gamma=0); mitigation recovers both devices -> psi=1.0 -> RESILIENT.
# Halt is suppressed while mitigation is pending/active (up to 3×baseline = 60 s).
#
#   psi = exp(-alpha_base × k_base)   (k_crit=0, threshold = theta_base)
#
#   Wave  Devices (both tau=1)             k_b  psi      region
#   1     right_wheels  [non-critical]      1    ≈0.819   tolerable     (delta=1, gamma=1)
#   2     +right_arm    [non-critical]      2    ≈0.670   NOT tolerable (delta=1, gamma=0)
#   ---   mitigation kicks in               0    1.000    recovered     (delta=1, gamma=1)
#
# Outputs (written by manual_run.py):
#   exp21.csv       — summary row (appended each run)
#   exp21_psi.csv   — psi sampled at 100 Hz
#   exp21_delta.csv — delta sampled at 100 Hz
#
# Usage:
#   ./auto_runs/data_exp21.sh
#   ./auto_runs/data_exp21.sh configs/experiment21.json ../results/framework_correctness/exp21.csv
#
set -u

cd "$(dirname "$0")/.."

DELAY="${DELAY:-10}"    # Webots load time
DELAY2="${DELAY2:-12}"  # Wave 1: right_wheels (tau=1, non-critical) — 2 s into task
DELAY3="${DELAY3:-17}"  # Wave 2: +right_arm (tau=1, non-critical) → psi crosses theta_base=0.72

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment21.json}"
RESULT="${2:-../results/framework_correctness/exp21.csv}"

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
  echo "[Wave 1 @ ${DELAY2}s]  $_yaml1  k_base=1 → psi≈0.819  (tolerable, delta=1, gamma=1)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" > /dev/null 2>&1 ) &

( sleep "$DELAY3"
  echo "[Wave 2 @ ${DELAY3}s]  $_yaml2  k_base=2 → psi≈0.670  (BELOW theta_base=0.72 → gamma=0, delta=1)"
  echo "  Mitigation pending: right_wheels + right_arm will be recovered"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" > /dev/null 2>&1 ) &

# --- wait and clean up -------------------------------------------------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"
echo "  psi timeline  : ${RESULT%.csv}_psi.csv"
echo "  delta timeline: ${RESULT%.csv}_delta.csv"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

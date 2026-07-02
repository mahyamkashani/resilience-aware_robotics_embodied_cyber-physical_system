#!/bin/bash
#
# data_exp_4b.sh — left wheels and arm attacks on navigate_to_goal (box2), WITH mitigation.
#
# Attacks 1 critical device (left_wheels, tau=1) and 1 non-critical device (left_arm, tau=1).
# alpha_base=0.20, theta_base=0.72, baseline=20 s.
# Wave 2 crosses theta_base (gamma=0); mitigation recovers both devices -> psi=1.0 -> RESILIENT.
# Halt is suppressed while mitigation is pending/active (up to 3x baseline = 60 s).
#
#   psi = exp(-alpha_base x k_base)   (both devices tau=1, k_crit=0)
#
#   Wave  Devices (both tau=1)         k_b  psi      region
#   1     left_wheels                   1    ~0.861   tolerable     (delta=1, gamma=1)
#   2     left_wheels+left_arm          2    ~0.741   NOT tolerable (delta=1, gamma=0)
#   ---   mitigation kicks in           0    1.000   recovered     (delta=1, gamma=1)

# Outputs (written by manual_run.py):
#   exp_4b.csv       -- summary row (appended each run)
#   exp_4b_psi.csv   -- psi sampled at 100 Hz
#   exp_4b_delta.csv -- delta sampled at 100 Hz
#
# Usage:
#   ./auto_runs/data_exp_4b.sh
#   ./auto_runs/data_exp_4b.sh configs/experiment_4b.json ../results/framework_correctness/exp_4b.csv
#
set -u

cd "$(dirname "$0")/.."

DELAY="${DELAY:-10}"    # Webots load time
DELAY2="${DELAY2:-12}"  # Wave 1: left_wheels (tau=1, critical) -- 2 s into task
DELAY3="${DELAY3:-17}"  # Wave 2: +left_arm (tau=1, non-critical) -> psi crosses theta_base=0.72

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment_4b.json}"
RESULT="${2:-../results/framework_correctness/exp_4b.csv}"

WAVE1="${WAVE1:-left_wheels:UNDERSPEED}"
WAVE2="${WAVE2:-left_wheels:UNDERSPEED,left_arm:UNDERSPEED}"

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
  echo "[Wave 1 @ ${DELAY2}s]  $_yaml1  k_base=1 -> psi~0.819  (tolerable, delta=1, gamma=1)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" > /dev/null 2>&1 ) &

( sleep "$DELAY3"
  echo "[Wave 2 @ ${DELAY3}s]  $_yaml2  k_base=2 -> psi~0.705  (BELOW theta_base=0.72 -> gamma=0, delta=1)"
  echo "  Mitigation pending: left_wheels + left_arm will be recovered"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" > /dev/null 2>&1 ) &

# --- wait and clean up -------------------------------------------------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"
echo "  psi timeline  : ${RESULT%.csv}_psi.csv"
echo "  delta timeline: ${RESULT%.csv}_delta.csv"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

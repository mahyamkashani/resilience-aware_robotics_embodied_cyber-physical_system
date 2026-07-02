#!/bin/bash
#
# data_exp12.sh — locomotion-only attack on navigate_and_pickup (table2).
#
# Mirrors exp15 attack type (left wheel tau=1 and left arm, tau=2) but with higher degradation
# (alpha_base=0.20, theta_base=0.72) so psi crosses theta_base → NOT TOLERABLE.
# No mitigation enabled → system cannot recover → task HALTED.
#
#   psi = exp(-alpha_crit × k_crit) × exp(-alpha_base × k_base)
#   alpha_crit=0.15, alpha_base=0.20, theta_crit=0.8, theta_base=0.72
#
#   Wave  Devices                      k_crit  psi      region
#   1     left_wheels (tau=2)          2       ≈0.741   BELOW theta_crit=0.8 → gamma=0
#   2     left_wheels + left_arm       4       ≈0.549   BELOW theta_base=0.72 → NOT TOLERABLE
#
# No mitigation possible → HALTED at 2×baseline_time = 97.6 s.
#
# Outputs (written automatically by manual_run.py):
#   exp_4a.csv       — summary row
#   exp_4a_psi.csv   — psi sampled at 100 Hz
#   exp_4a_delta.csv — delta sampled at 100 Hz
#
# Usage:
#   ./auto_runs/data_exp_4a.sh
#   ./auto_runs/data_exp_4a.sh configs/experiment_4a.json ../results/framework_correctness/exp_4a.csv
#
set -u

cd "$(dirname "$0")/.."

DELAY="${DELAY:-5}"     # Webots load time
DELAY2="${DELAY2:-8}"   # Wave 1: left_wheels → psi crosses theta_crit
DELAY3="${DELAY3:-15}"  # Wave 2: left_arm added → psi crosses theta_base → NOT TOLERABLE

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment_4a.json}"
RESULT="${2:-../results/framework_correctness/exp_4a.csv}"

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

# --- 3) inject escalating wheel attacks --------------------------------------
( sleep "$DELAY2"
  echo "[Wave 1 @ ${DELAY2}s]  $_yaml1"
  echo "  k_crit=2 → psi≈0.741  (BELOW theta_crit=0.80 → gamma=0, not tolerable if critical)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" > /dev/null 2>&1 ) &

( sleep "$DELAY3"
  echo "[Wave 2 @ ${DELAY3}s]  $_yaml2"
  echo "  k_crit=4 → psi≈0.549  (BELOW theta_base=0.72 → NOT TOLERABLE, gamma=0)"
  echo "  No mitigation available → system will HALT at 2×baseline (97.6 s)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" > /dev/null 2>&1 ) &

# --- wait for the experiment to finish, then shut Webots down ----------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"
echo "  psi timeline  : ${RESULT%.csv}_psi.csv"
echo "  delta timeline: ${RESULT%.csv}_delta.csv"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

#!/bin/bash
#
# data_exp8.sh — single permanent attack on a critical non-mitigatable device.
#
# Config: experiment8.json
#   - Only non-critical devices (right_arm, right_gripper) are mitigatable.
#   - left_wheels is critical (tau=2) and NOT in the mitigatable set.
#
# Result:
#   - After Wave 1, left_wheels enters S → delta=0 permanently.
#   - mitigation_feasability returns feasible=0 (no subset can clear a
#     non-mitigatable critical device from S_effective).
#   - System stays NOT RESILIENT until halt (2× baseline_time).
#
#   Wave  Device        tau  mitigatable  psi                       delta
#   1     left_wheels   2    NO           exp(-0.4×1) ≈ 0.670 < θ   0 (permanent)
#
# Outputs (written automatically by manual_run.py):
#   exp8.csv       — summary row
#   exp8_psi.csv   — psi sampled at 100 Hz
#   exp8_delta.csv — delta sampled at 100 Hz
#
# Usage:
#   ./data_exp8.sh
#   ./data_exp8.sh configs/experiment8.json ../results/framework_correctness/exp8.csv
#
set -u

cd "$(dirname "$0")"

DELAY="${DELAY:-5}"    # Webots load time
DELAY2="${DELAY2:-20}"  # Wave 1 — inject 3 s after controller starts (wall clock)

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment8.json}"
RESULT="${2:-../results/framework_correctness/exp8.csv}"

WAVE1="left_wheels:STOP"

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

# --- 3) single permanent attack ----------------------------------------------
( sleep "$DELAY2"
  echo "[Wave 1 @ ${DELAY2}s]  left_wheels:STOP  (critical, NOT mitigatable)"
  echo "  → delta drops to 0 and stays there; system halts at 2× baseline"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: ['left_wheels:STOP']}" > /dev/null 2>&1 ) &

# --- wait for the experiment to finish, then shut Webots down ----------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"
echo "  psi timeline : ${RESULT%.csv}_psi.csv"
echo "  delta timeline: ${RESULT%.csv}_delta.csv"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

#!/bin/bash
#
# data_exp13.sh — three escalating wheel-focused attack waves, task: navigate_to_goal box2.
#
# baseline_time=17.5 s  →  HALT fires at 35 s simulation time (2×baseline).
# Mitigation is active for both wheels so early waves are neutralised.
# Third wave keeps both wheels stopped long enough that psi drops below theta_crit.
#
#   psi = exp(-alpha_crit × k_crit) × exp(-alpha_base × k_base)
#   alpha_crit=0.08, alpha_base=0.04, theta_crit=0.8
#
#   Wave  Devices                          k_c  psi      region
#   1     left_wheels (tau=2)              1    ≈0.923   tolerable → mitigated
#   2     left_wheels + right_wheels       2    ≈0.852   tolerable → mitigated
#   3     left_wheels + right_wheels       2    ≈0.852   sustained; psi may cross threshold
#
# Outputs (written by manual_run.py):
#   exp13.csv       — summary row (appended each run)
#   exp13_psi.csv   — psi sampled at 100 Hz
#   exp13_delta.csv — delta sampled at 100 Hz
#
# Usage:
#   ./auto_runs/data_exp13.sh
#   ./auto_runs/data_exp13.sh configs/experiment13.json ../results/framework_correctness/exp13.csv
#   DELAY2=8 DELAY3=13 ./auto_runs/data_exp13.sh
#
set -u

cd "$(dirname "$0")/.."

DELAY="${DELAY:-10}"    # Webots load time — 10 s to be safe on slower/repeated starts
DELAY2="${DELAY2:-12}"  # Wave 1: 2 s into task (task starts at t=10 s)
DELAY3="${DELAY3:-17}"  # Wave 2: 7 s into task
DELAY4="${DELAY4:-22}"  # Wave 3: 12 s into task — escalation near task end

WORLD="my_webot_project/worlds/my_project_world.wbt"
CONTROLLER="my_webot_project/controllers/manual_run.py"

CONFIG="${1:-configs/experiment13.json}"
RESULT="${2:-../results/framework_correctness/exp13.csv}"

WAVE1="${WAVE1:-left_wheels:STOP}"
WAVE2="${WAVE2:-left_wheels:STOP,right_wheels:STOP}"
WAVE3="${WAVE3:-left_wheels:STOP,right_wheels:STOP,left_gripper:STOP,right_gripper:STOP}"

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
  echo "  k_crit=1 → psi≈0.923  (tolerable, mitigation will neutralise)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml1}" > /dev/null 2>&1 ) &

( sleep "$DELAY3"
  echo "[Wave 2 @ ${DELAY3}s]  $_yaml2"
  echo "  k_crit=2 → psi≈0.852  (tolerable, mitigation active for both wheels)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml2}" > /dev/null 2>&1 ) &

( sleep "$DELAY4"
  echo "[Wave 3 @ ${DELAY4}s]  $_yaml3"
  echo "  k_crit=3, k_base=1 → psi≈0.757  (BELOW theta_crit=0.80 → gamma=0)"
  echo "  Arms not mitigatable → system HALTED at 2×baseline (97.6 s)"
  ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
    "{compromised_devices: $_yaml3}" > /dev/null 2>&1 ) &

# --- wait for the experiment to finish, then shut Webots down ----------------
wait "$SIM_PID"
echo "Experiment finished; results written to $RESULT"
echo "  psi timeline  : ${RESULT%.csv}_psi.csv"
echo "  delta timeline: ${RESULT%.csv}_delta.csv"

kill "$WEBOTS_PID" 2>/dev/null
echo "Scenario complete; Webots closed."

# Implementation and Evaluation of Cyber-Physical Embodied System under Device-level Cyberattacks

## Installation

```bash
cd ~/ros2_ws
colcon build --packages-select my_attack_interfaces
source install/setup.bash
colcon build --packages-select attack_pkg
source install/setup.bash
```

## Execution

Open **3 separate terminals** and run one command in each.

**Terminal 1: Webots simulation without PR2 controller:**
```bash
cd ~/ros2_ws && source install/setup.bash
webots ~/my_webot_project/worlds/my_project_world.wbt
```

**Terminal 2: Run PR2 controller using JSON configuration file:**
```bash
python3 ~/my_webot_project/controllers/manual_run.py
```
or
```bash
python3 ~/my_webot_project/controllers/pr2_controller/pr2_controller.py  ~/my_webot_project/controllers/pr2_controller/configs/experiment2.json
```

**Terminal 3: Attack node:**
```bash
cd ~/ros2_ws && source install/setup.bash
ros2 run attack_pkg attack_node
```

**Terminal 4: Trigger an attack:**
```bash
cd ~/ros2_ws && source install/setup.bash
ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
  "{compromised_devices: ['right_wheels:STOP']}"
```

**Terminal 5: Stop all attacks:**
```bash
ros2 topic pub --once /active_attacks my_attack_interfaces/msg/AttackState \
  "{compromised_devices: []}"
```
### Available Attacks

| Component | Attack Types |
|---|---|
| `left_wheels`, `right_wheels` | `STOP`, `OVERSPEED`, `UNDERSPEED`, `BACKWARD` |
| `left_arm`, `right_arm` | `STOP`, `OVERSPEED`, `UNDERSPEED`, `BACKWARD` |
| `left_gripper`, `right_gripper` | `STOP`, `OVERSPEED`, `UNDERSPEED`, `BACKWARD`, `GRIP_WEAK` |
| `torso`, `head` | `STOP`, `OVERSPEED`, `UNDERSPEED`, `BACKWARD` |

### Automated Execution

Instead of the manual multi-terminal flow above, `run_scenario.sh` automates a full
run: it launches Webots, starts the PR2 controller after a delay, injects an attack,
waits for the experiment to finish, records the result CSV, and shuts Webots down.

```bash
cd ~/ros2_ws && source install/setup.bash   # ensure ROS 2 is sourced
./run_scenario.sh [config] [attack] [result]
```

All arguments are optional and have defaults (experiment2 + `left_gripper:GRIP_WEAK`):

```bash
# Defaults
./run_scenario.sh

# A specific experiment + non-resilient attack
./run_scenario.sh configs/experiment2.json "left_arm:STOP" ../results/framework_correctness/exp2.csv

# Multiple compromised devices
./run_scenario.sh configs/experiment4.json "left_wheels:STOP,right_wheels:STOP"
```

Launch timing is configurable via the `DELAY` (controller start) and `DELAY2`
(attack injection) environment variables, in seconds:

```bash
DELAY=8 DELAY2=15 ./run_scenario.sh configs/experiment2.json "left_arm:STOP"
```

To collect all results in one go:

```bash
for n in 1 2 4; do
  ./run_scenario.sh "configs/experiment$n.json" "left_arm:STOP" "../results/framework_correctness/exp$n.csv"
done
```

## Testing

Unit tests live in `my_webot_project/controllers/tests/tests.py` and cover the degradation metric (`metrics.Metrics.compute_degradation`), including the
edge cases where task execution time is negative (a task finishing faster than its baseline, or halting before completion).

Run them with `pytest` from the `tests` directory:

```bash
cd ~/my_webot_project/controllers/tests
pytest tests.py -v
```

## Acknoweledgement

This project is modification of simulation and resilicient-aware robotics cyber-physical system developed by Gysella Imrell. Link to initial version: https://github.com/GysellaImrell/examensarbete

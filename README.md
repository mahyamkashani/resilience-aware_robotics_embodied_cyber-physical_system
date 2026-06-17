# Implementation and Evaluation of CP Embodied System under Device-level Cyberattacks

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

## Testing

Unit tests live in `my_webot_project/controllers/tests/tests.py` and cover the
degradation metric (`metrics.Metrics.compute_degradation`), including the
edge cases where task execution time is negative (a task finishing faster than
its baseline, or halting before completion).

Run them with `pytest` from the `tests` directory:

```bash
cd ~/my_webot_project/controllers/tests
pytest tests.py -v
```


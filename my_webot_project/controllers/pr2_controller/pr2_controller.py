'''
Goal
- Read JSON config
- Set task, tau, epsilopn, kappa
- Set thresholds (theta_crit and theta_base)
- Listen for attacks via ROS 2
'''
import rclpy
import sys 
import json
import os
from controller import Supervisor

from resilience_manager import ResilienceManager
from ids import IDS
import task
from pr2_control import WHEEL_NAMES, LEFT_ARM_NAMES, RIGHT_ARM_NAMES, LEFT_FINGER_MOTOR, RIGHT_FINGER_MOTOR
from attack_executor import AttackExecutor
from component_mapping import COMPONENT_MAP
from ros2_subscriber import SubscriberNode

# ---------------------
# Load Conig
# ---------------------
#base_dir = os.path.dirname(__file__)
config_path = sys.argv[1]
print(config_path)
with open(config_path) as f:
    config = json.load(f)

# ----------------------
# Webot Setup
# ----------------------
supervisor = Supervisor()
timestep = int(supervisor.getBasicTimeStep())

# ---------------------
# ROS2 setup
# ---------------------
rclpy.init()
subscriber_node = SubscriberNode()

#-----------------------
# Init core modules
# ----------------------
devices = WHEEL_NAMES + LEFT_ARM_NAMES + RIGHT_ARM_NAMES + [LEFT_FINGER_MOTOR, RIGHT_FINGER_MOTOR]

RM = ResilienceManager(devices)
ids = IDS(devices)
attack_executor = AttackExecutor(supervisor, COMPONENT_MAP)

# ------------------------
# Task Setup 
# ------------------------
task_type = config["task"]["type"]
goal_pos_name = config["task"]["goal"]
object_name = config["task"]["object"]
arm = config["task"]["arm"]

# Select task function
if task_type == "navigate":
    current_task = task.navigate_to_goal

elif task_type == "pickup":
    current_task = task.pickup_object

elif task_type == "navigate_and_pickup":
    current_task = task.navigagte_and_pickup_object

else:
    raise ValueError(f"Unknown task type: {task_type}")

# Waypoints from Webots
waypoints = {}
waypoints[goal_pos_name] = supervisor.getFromDef(goal_pos_name).getPosition()


# ------------------------------
# Build tau / epsilon / kappa
# ------------------------------
task_name = task_type
goal_name = goal_pos_name

tau = {}
epsilon  = {}
kappa = {}

for comp, val in config["tau"].items():
    tau[(comp, task_name)] = val

for comp, val in config["epsilon"].items():
    epsilon[(comp, goal_name)] = val

for comp, val in config["kappa"].items():
    kappa[(comp)] = val

RM.load_example(
    tau,
    epsilon,
    kappa,
    task_name,
    goal_name
)

# -----------------------------
# Thresholds (theta & alpha)
# -----------------------------
RM.theta_crit = config["thresholds"]["theta_crit"]
RM.theta_base = config["thresholds"]["theta_base"]
RM.alpha_crit = config["thresholds"]["alpha_crit"]
RM.alpha_base = config["thresholds"]["alpha_base"]

# ----------------------
# Mitigation
# ----------------------
RM.mitigatable_devices = set(config["mitigation"]["enabled_devices"])


# ------------------------
# Resilience Check
# ------------------------
def check_resilience_live():
    # Process ROS 2 attacks
    rclpy.spin_once(subscriber_node, timeout_sec=0)
    attack_executor.update(subscriber_node.attack_state)
    attack_executor.apply()

    # Update IDS
    #compromised = [a["component"] for a in attack_executor.active_attacks]
    ids.update_attack_state(subscriber_node.attack_state)
    ids_output = ids.get_probability_output()

    # Update S in RM
    RM.update_compromised_set(ids_output)

    # Check resilience
    result, neutralized = RM.check_resilience()

    # Neutralize attack executor
    if neutralized:
        attack_executor.neutralized(neutralized)

    # Log transitions
    RM.log_state_changes()

    return result

# -------------------------------
# Execute task
# -------------------------------
if task_type == "navigate":
    result = current_task(
        supervisor,
        waypoints,
        goal_name,
        timestep,
        resilience_check=check_resilience_live,
        resilience_manager=RM,
        attack_executor=attack_executor,
        avoid_obstacles=config.get("obstacle_avoidance", False),
    )

elif task_type == "pickup":
    result = current_task(
        supervisor,
        arm,
        object_name,
        timestep,
        resilience_check=check_resilience_live,
        resilience_manager=RM,
        attack_executor=attack_executor
    )

elif task_type == "navigate_and_pickup":
    result = current_task(
        supervisor,
        waypoints,
        goal_name,
        arm,
        object_name,
        timestep,
        resilience_check=check_resilience_live,
        resilience_manager=RM,
        attack_executor=attack_executor,
        avoid_obstacles=config.get("obstacle_avoidance", False),
    )

print(f"Task result: {result}")


# ---------------
# Webot main loop
# ---------------
while supervisor.step(timestep) != -1:
    pass

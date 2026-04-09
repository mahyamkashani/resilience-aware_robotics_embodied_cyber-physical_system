import rclpy
from controller import Supervisor
from ros2_subscriber import SubscriberNode
from resilience_manager import ResilienceManager
from ids import IDS
from examples import navigate, pickup_object, navigagte_and_pickup_object
import task
from pr2_control import WHEEL_NAMES, LEFT_ARM_NAMES, RIGHT_ARM_NAMES
from attack_executor import AttackExecutor
from component_mapping import COMPONENT_MAP

# Webot Setup
supervisor = Supervisor()
timestep = int(supervisor.getBasicTimeStep())

# ROS init and Node instance
rclpy.init()
sub_node = SubscriberNode()

# Init attack executor
attack_executor = AttackExecutor(supervisor, COMPONENT_MAP)

# Task Setup ----------------------------------------------

# Task setup
current_task = navigagte_and_pickup_object

goal_name = "table2"
object_name = "water_bottle" 

# Waypoints from Webots
current_task["waypoints"][goal_name] = supervisor.getFromDef(goal_name).getPosition()

arm = pickup_object["arm"]
#test_example["waypoints"][goal_name] = supervisor.getFromDef(goal_name).getPosition()

# Load all devices into RM
devices = WHEEL_NAMES + LEFT_ARM_NAMES + RIGHT_ARM_NAMES
resilience_manager = ResilienceManager(devices)

# Load task info into RM
resilience_manager.load_example(
    current_task["tau"],
    current_task["epsilon"],
    current_task["kappa"],
    next(iter(current_task["T"])),
    next(iter(current_task["G"]))
)


# Load IDS with devices from RM --------------------------
ids = IDS(resilience_manager.D)


# Resilience check ---------------------------------------
def check_resilience_live():
    rclpy.spin_once(sub_node, timeout_sec=0.0)

    # apply attack effect
    attack_executor.update(sub_node.attack_state)
    attack_executor.apply()

    # Update IDS
    ids.update_attack_state(sub_node.attack_state)
    ids_output = ids.get_probability_output()

    # Update S
    resilience_manager.update_compromised_set(ids_output)

    # Check resilience
    result, neutralized = resilience_manager.check_resilience()

    # Neutralize attack executor
    if neutralized:
        attack_executor.neutralized(neutralized)

    # Log transitions
    resilience_manager.log_state_changes()

    
    return result

'''
# Execute current task
result_navigate = task.navigate_to_goal(
    supervisor,
    navigate["waypoints"],
    goal_name=goal_name,
    timestep=timestep,
    resilience_check=check_resilience_live,
    resilience_manager=resilience_manager,
    attack_executor=attack_executor
)
print(f"Navigate task: {result_navigate}")

'''
'''
# Execute pickup task
result_pickup = task.pickup_object(
    supervisor,
    object_name=object_name,
    arm=arm,
    timestep=timestep,
    resilience_check=check_resilience_live,
    resilience_manager=resilience_manager,
    attack_executor=attack_executor
)
print(f"Pick up task: {result_pickup}")
'''

# Execute pickup task
result_navigate_pickup = task.navigagte_and_pickup_object(
    supervisor,
    waypoints=current_task["waypoints"],
    goal_name=goal_name,
    arm=arm,
    object_name=object_name,
    timestep=timestep,
    resilience_check=check_resilience_live,
    resilience_manager=resilience_manager,
    attack_executor=attack_executor
)
print(f"Pick up and navigate task: {result_navigate_pickup}")

# Webot main loop
while supervisor.step(timestep) != -1:
    rclpy.spin_once(sub_node, timeout_sec=0.0)

sub_node.destroy_node()
rclpy.shutdown()


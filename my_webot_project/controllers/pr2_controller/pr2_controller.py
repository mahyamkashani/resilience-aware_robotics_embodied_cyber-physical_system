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
from controller import Supervisor

from resilience_manager import ResilienceManager
from ids import IDS
import task
from pr2_hardware_control import WHEEL_NAMES, LEFT_ARM_NAMES, RIGHT_ARM_NAMES, LEFT_FINGER_MOTOR, RIGHT_FINGER_MOTOR
from attack_executor import AttackExecutor
from component_mapping import COMPONENT_MAP, map_to_high_level
from disruption_degradation import monotonic_degradation

try:
    from ros2_subscriber import SubscriberNode
except ImportError:
    SubscriberNode = None


def run_simulation(config_path, use_ros=True):
    # ---------------------
    # Load Config
    # ---------------------
    #config_path = sys.argv[1]
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
    if use_ros and SubscriberNode is not None:
        rclpy.init()
        subscriber_node = SubscriberNode()
    else:
        subscriber_node = None

    #-----------------------
    # Init core modules
    # ----------------------
    devices = set(COMPONENT_MAP.keys()) # High level representation of robot devices
    #print(devices)
    #WHEEL_NAMES + LEFT_ARM_NAMES + RIGHT_ARM_NAMES + [LEFT_FINGER_MOTOR, RIGHT_FINGER_MOTOR]

    RM = ResilienceManager(devices)
    ids = IDS(devices)
    attack_executor = AttackExecutor(supervisor, COMPONENT_MAP)

    # ------------------------
    # Task Setup 
    # ------------------------
    task_type = config["task"]["type"]
    goal_pos_name = config["task"].get("goal")
    object_name = config["task"].get("object")
    arm = config["task"].get("arm")

    # Select task function
    if task_type == "navigate_to_goal":
        current_task = task.navigate_to_goal

    elif task_type == "pickup_object":
        current_task = task.pickup_object

    elif task_type == "navigate_and_pickup":
        current_task = task.navigate_and_pickup_object

    else:
        raise ValueError(f"Unknown task type: {task_type}")

    # Waypoints from Webots
    waypoints = {}
    if goal_pos_name:
        waypoints[goal_pos_name] = supervisor.getFromDef(goal_pos_name).getPosition()


    # ------------------------------
    # Build tau / epsilon / kappa
    # ------------------------------
    task_name = task_type
    goal_name = goal_pos_name

    tau = {}
    epsilon  = {}

    for comp, val in config["tau"].items():
        tau[(comp, task_name)] = val

    for comp, val in config["epsilon"].items():
        epsilon[(comp, goal_name)] = val


    RM.load_example(
        tau,
        epsilon,
        task_name,
        goal_name
    )

    # -----------------------------
    # Thresholds (theta, alpha, baseline time and mitigation delay)
    # -----------------------------
    RM.theta_crit = config["thresholds"]["theta_crit"]
    RM.theta_base = config["thresholds"]["theta_base"]
    RM.alpha_crit = config["thresholds"]["alpha_crit"]
    RM.alpha_base = config["thresholds"]["alpha_base"]
    RM.baseline_time = config.get("baseline_time", None)
    RM.mitigation_delay_steps  = config.get("mitigation_delay_steps", 0)

    # -----------------------------
    # Information for IDS
    # -----------------------------
    ids.kappa_crit = config["thresholds"]["kappa_crit"]
    ids.kappa_base = config["thresholds"]["kappa_base"]
    ids.tau = tau
    ids.epsilon = epsilon
    ids.current_task = task_name
    ids.current_goal = goal_name

    # ----------------------
    # Mitigation
    # ----------------------
    RM.mitigatable_devices = set(config["mitigation"]["enabled_devices"])


    # Used if tests were run automatically..
    def generate_attacks():
        return [
            {"component": "left_gripper", "type": "GRIP_WEAK"}
        ]


    # ------------------------
    # Resilience Check
    # ------------------------
    def check_resilience_live():
        
        if use_ros and subscriber_node is not None:
            rclpy.spin_once(subscriber_node, timeout_sec=0)
            active_attacks = subscriber_node.active_attacks
        else:
            active_attacks = generate_attacks()

        RM.current_attacks = active_attacks

        attack_executor.update(active_attacks)
        attack_executor.apply()

        # Update IDS
        components = {attack["component"] for attack in active_attacks}
        ids.update_attack_state(components)

        # High level representation of components -> pass to RM
        #S_high = map_to_high_level(ids.S, COMPONENT_MAP)
        RM.S = ids.S

        # Check resilience
        result, neutralized = RM.check_resilience()

        #print(neutralized)

        # Neutralize attack executor update S via IDS
        if neutralized:
            subscriber_node.active_attacks = [
                attack for attack in subscriber_node.active_attacks
                if attack["component"] not in neutralized
            ]
            attack_executor.neutralized(neutralized)
            for comp in neutralized:
                ids.clear_device(comp)

        # Log transitions
        RM.log_state_changes()
        return result

    # -------------------------------
    # Execute task
    # -------------------------------
    
    RM.start_time = supervisor.getTime() 

    if task_type == "navigate_to_goal":
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

    elif task_type == "pickup_object":
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

    end_time = supervisor.getTime()
    elapsed_time = end_time - RM.start_time

    print(f"Task result: {result}")
    #print(f"Execution time: {elapsed_time:.1f} seconds")


    baseline_time = config.get("baseline_time", None)

    if result != "Done": # HALTED
        degradation = None
        print(f"Task {result} after {elapsed_time:.1f}s did not complete")
    elif baseline_time:
        slowdown = elapsed_time - baseline_time
        degradation = max(0, slowdown / baseline_time)
        print(f'Task execution time increased with {slowdown:.1f} seconds')
        print(f'Degradation: {degradation * 100:.1f}%')
    else:
        degradation = None
        print(f'Task execution time: {elapsed_time:.1f} seconds (no baseline configured)')


    psi = monotonic_degradation(
        RM.S,
        RM.tau,
        RM.epsilon,
        RM.current_task,
        RM.current_goal,
        RM.alpha_crit,
        RM.alpha_base
    )

    #print(f"psi={psi}, theta={RM.theta_base}, gamma={RM.current_gamma}")

    return {
        "delta": RM.current_delta,
        "gamma": RM.current_gamma,
        "resilient": RM.current_resilient,
        "result": result,
        "time": elapsed_time,
        "degradation": degradation,
        "kappa_crit": ids.kappa_crit,
        "theta_base": RM.theta_base,
        "alpha_base": RM.alpha_base,
        "psi": psi
    }


if __name__ == "__main__":
    import sys
    run_simulation(sys.argv[1])
'''
Goal
- Read JSON config
- Set task, tau, epsilopn, kappa
- Set thresholds (theta_crit and theta_base)
- Listen for attacks via ROS 2
'''
import os
import rclpy
import sys
import json
from controller import Supervisor

from resilience_manager import ResilienceManager
from ids import IDS
import task
from constants import AttackType
from attack_executor import AttackExecutor
from component_mapping import COMPONENT_MAP, map_to_high_level
from disruption_degradation import monotonic_degradation, exponential_degradation, disruption
from metrics import Metrics
from logger import log_psi, log_delta

try:
    from ros2_subscriber import SubscriberNode
except ImportError:
    SubscriberNode = None


def run_simulation(config_path, use_ros=True, psi_log_path=None, delta_log_path=None):
    # Clear stale log files so each run starts with a fresh timeline
    for path in (psi_log_path, delta_log_path):
        if path and os.path.isfile(path):
            os.remove(path)

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
    RM.event_log_path = config.get("event_log", None)  # set in config to log the attack→mitigation flow to CSV

    # -----------------------------
    # Information for IDS
    # -----------------------------
    ids.kappa_crit = config["thresholds"]["kappa_crit"]
    ids.kappa_base = config["thresholds"]["kappa_base"]
    ids.tau = tau
    ids.epsilon = epsilon
    ids.current_task = task_name
    ids.current_goal = goal_name
    ids.detection_delay_steps = config.get("detection_delay_steps", 0)

    # -----------------------------
    # Degradation function selection
    # -----------------------------
    degradation_mode = config.get("degradation_mode", "monotonic")
    RM.psi_fn = exponential_degradation if degradation_mode == "exponential" else monotonic_degradation

    # ----------------------
    # Mitigation
    # ----------------------
    RM.mitigatable_devices = set(config["mitigation"]["enabled_devices"])


    # Used if tests were run automatically..
    def generate_attacks():
        return [
            {"component": "left_gripper", "type": AttackType.GRIP_WEAK}
        ]


    # ------------------------
    # Resilience Check
    # ------------------------
    _last_psi_second = [-1]

    def check_resilience_live():
        if use_ros and subscriber_node is not None:
            rclpy.spin_once(subscriber_node, timeout_sec=0)
            active_attacks = subscriber_node.active_attacks
        else:
            active_attacks = generate_attacks()

        RM.current_attacks = active_attacks

        attack_executor.update(active_attacks)
        attack_executor.apply(resilience_manager=RM)

        # Update IDS
        components = {attack["component"] for attack in active_attacks}
        ids.update_attack_state(components)
        ids.tick_detection_timer()

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
        RM.log_state_changes(supervisor.getTime())

        # Log psi and delta at 100 Hz (0.01 s resolution) to separate CSVs
        if psi_log_path or delta_log_path:
            current_tick = round(supervisor.getTime() * 100)
            if current_tick != _last_psi_second[0]:
                _last_psi_second[0] = current_tick
                t = current_tick / 100.0
                if psi_log_path:
                    psi_now = RM.psi_fn(
                        RM.S, RM.tau, RM.epsilon,
                        RM.current_task, RM.current_goal,
                        RM.alpha_crit, RM.alpha_base,
                    )
                    log_psi(psi_log_path, t, psi_now)
                if delta_log_path:
                    delta_now = disruption(
                        RM.S, RM.tau, RM.epsilon,
                        RM.current_task, RM.current_goal,
                    )
                    operation = "NORMAL" if delta_now == 1 else "DISRUPTED"
                    log_delta(delta_log_path, t, delta_now, operation)

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

    # A task that technically finished while the system is NOT RESILIENT
    # doesn't count as a genuine success — downgrade it to HALTED.
    if result == "DONE" and RM.current_resilient == "NOT RESILIENT":
        result = "HALTED"

    end_time = supervisor.getTime()

    # Append final task result marker to delta log
    if delta_log_path:
        log_delta(delta_log_path, round(end_time, 2), "-", result)
    elapsed_time = end_time - RM.start_time

    print(f"Task result: {result}")
    #print(f"Execution time: {elapsed_time:.1f} seconds")


    baseline_time = config.get("baseline_time", None)
    degradation, slowdown = Metrics().compute_degradation(result, elapsed_time, baseline_time)

    if result != "DONE": # HALTED
        print(f"Task {result} after {elapsed_time:.1f}s did not complete")
    elif baseline_time:
        if slowdown >= 0:
            print(f'Task execution time increased with {slowdown:.1f} seconds')
        else:
            print(f'Task finished {abs(slowdown):.1f} seconds faster than baseline')
        print(f'Degradation: {degradation * 100:.1f}%')
    else:
        print(f'Task execution time: {elapsed_time:.1f} seconds (no baseline configured)')


    psi = RM.psi_fn(
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
        "theta_crit": RM.theta_crit,
        "alpha_base": RM.alpha_base,
        "psi": psi,
        "devices": ids.S,
    }


if __name__ == "__main__":
    import sys
    run_simulation(sys.argv[1])
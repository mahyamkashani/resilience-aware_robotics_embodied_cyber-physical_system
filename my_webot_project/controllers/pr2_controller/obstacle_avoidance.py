import math
from components.distance_sensor import DistanceSensor
import pr2_hardware_control as pr2

AVOIDANCE_THRESHOLD = 0.50   # closeness score to start reacting  → ~1.0 m away
STOP_THRESHOLD      = 0.75   # closeness score on BOTH sides → ~0.5 m away (emergency)
STRAFE_DISTANCE     = 0.5           # metres to strafe sideways per avoidance step
STEP_DISTANCE       = 0.35          # metres per forward micro-step
GOAL_TOLERANCE      = 0.30          # metres — stop when this close to goal
HEADING_TOLERANCE   = 0.10          # radians — skip re-orient if error is small
NEAR_GOAL_ZONE      = 1.2           # metres — disable avoidance inside this radius around goal


def init_sensors(supervisor, timestep):
    left  = DistanceSensor(supervisor, "ds_left",  timestep)
    right = DistanceSensor(supervisor, "ds_right", timestep)
    left.enable()
    right.enable()
    return left, right


def _read(ds_left, ds_right):
    return ds_left.sensor.getValue(), ds_right.sensor.getValue()


def _robot_heading_error(supervisor, goal_pos):
    robot_pos = supervisor.getSelf().getPosition()
    dx = goal_pos[0] - robot_pos[0]
    dy = goal_pos[1] - robot_pos[1]
    angle_to_goal = math.atan2(dy, dx)
    rot = supervisor.getSelf().getField("rotation").getSFRotation()
    ax, ay, az, angle = rot
    robot_angle = angle * az
    error = angle_to_goal - robot_angle
    while error >  math.pi: error -= 2 * math.pi
    while error < -math.pi: error += 2 * math.pi
    return error


def _dist_to_goal(supervisor, goal_pos):
    pos = supervisor.getSelf().getPosition()
    return math.sqrt((goal_pos[0] - pos[0])**2 + (goal_pos[1] - pos[1])**2)


def navigate_with_avoidance(supervisor, goal_pos, timestep, ds_left, ds_right,
                             goal_node=None, resilience_check=None,
                             resilience_manager=None, attack_executor=None):

    while True:
        # ── Goal reached? ──────────────────────────────────────────────
        if _dist_to_goal(supervisor, goal_pos) < GOAL_TOLERANCE:
            pr2.stop_wheels(supervisor)
            return "DONE"

        if goal_node and len(goal_node.getContactPoints()) > 0:
            pr2.stop_wheels(supervisor)
            return "DONE"

        # ── Resilience check ───────────────────────────────────────────
        if resilience_check:
            if not resilience_check():
                if not (resilience_manager and resilience_manager.pending_mitigation) and \
                   not (attack_executor and attack_executor.has_active_attacks()):
                    pr2.stop_wheels(supervisor)
                    return "HALTED"

        # ── Read sensors (skip avoidance near goal to avoid treating it as obstacle) ──
        dist_to_goal = _dist_to_goal(supervisor, goal_pos)
        left_close, right_close = _read(ds_left, ds_right)

        if dist_to_goal < NEAR_GOAL_ZONE:
            left_close, right_close = 0.0, 0.0

        if left_close > STOP_THRESHOLD and right_close > STOP_THRESHOLD:
            # Imminent collision on both sides: back up, then strafe toward clearer side
            pr2.stop_wheels(supervisor)
            pr2.robot_go_forward(supervisor, -0.3, timestep)
            strafe = STRAFE_DISTANCE if right_close >= left_close else -STRAFE_DISTANCE
            pr2.robot_go_sideways(supervisor, strafe, timestep)

        elif left_close > AVOIDANCE_THRESHOLD or right_close > AVOIDANCE_THRESHOLD:
            # Obstacle on one side: strafe away from it
            pr2.stop_wheels(supervisor)
            # obstacle on left → strafe right (negative), obstacle on right → strafe left (positive)
            strafe = -STRAFE_DISTANCE if left_close > right_close else STRAFE_DISTANCE
            pr2.robot_go_sideways(supervisor, strafe, timestep,
                                  resilience_check, resilience_manager, attack_executor)

        else:
            # Clear path: re-orient toward goal if needed, then drive a step
            error = _robot_heading_error(supervisor, goal_pos)
            if abs(error) > HEADING_TOLERANCE:
                pr2.robot_rotate(supervisor, error, timestep,
                                 resilience_check, resilience_manager, attack_executor)

            step = min(STEP_DISTANCE, _dist_to_goal(supervisor, goal_pos))
            result = pr2.robot_go_forward(supervisor, step, timestep,
                                          resilience_check, resilience_manager,
                                          goal_node, attack_executor)
            if result == "HALTED":
                return "HALTED"

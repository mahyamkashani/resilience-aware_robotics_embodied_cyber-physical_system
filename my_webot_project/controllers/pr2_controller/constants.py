from enum import Enum


# ---------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------
class Side(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class AttackType(str, Enum):
    STOP = "STOP"
    OVERSPEED = "OVERSPEED"
    UNDERSPEED = "UNDERSPEED"
    BACKWARD = "BACKWARD"
    GRIP_WEAK = "GRIP_WEAK"
    GRIP_STRONG = "GRIP_STRONG"



ATTACK_SEVERITY = {
    AttackType.STOP: 1.0,
    AttackType.OVERSPEED: 1.0, #0.6,
    AttackType.UNDERSPEED: 1.0, #0.4,
    AttackType.BACKWARD: 1.0, #0.6,
    AttackType.GRIP_WEAK: 1.0, #0.5,
    AttackType.GRIP_STRONG: 1.0, #0.5,
}


# ----------------------------------------------------------------------
# Manual-run defaults
# ----------------------------------------------------------------------
CONFIG = "configs/experiment2.json"
RESULT_FILE = "../results/framework_correctness/exp1.csv"


# ----------------------------------------------------------------------
# PR2 hardware constants
# ----------------------------------------------------------------------
MAX_WHEEL_SPEED = 4.0         # maximum velocity for the wheels [rad / s]
WHEELS_DISTANCE = 0.4492      # distance between 2 caster wheels (the four wheels are located in square) [m]
SUB_WHEELS_DISTANCE = 0.098   # distance between 2 sub wheels of a caster wheel [m]
WHEEL_RADIUS = 0.08           # wheel radius
TOLERANCE = 0.05

WHEEL_NAMES = [
    "fl_caster_l_wheel_joint",
    "fl_caster_r_wheel_joint",
    "fr_caster_l_wheel_joint",
    "fr_caster_r_wheel_joint",
    "bl_caster_l_wheel_joint",
    "bl_caster_r_wheel_joint",
    "br_caster_l_wheel_joint",
    "br_caster_r_wheel_joint",
]

ROTATION_NAMES = [
    "fl_caster_rotation_joint",
    "fr_caster_rotation_joint",
    "bl_caster_rotation_joint",
    "br_caster_rotation_joint",
]

RIGHT_ARM_NAMES = [
    "r_shoulder_pan_joint",
    "r_shoulder_lift_joint",
    "r_upper_arm_roll_joint",
    "r_elbow_flex_joint",
    "r_wrist_roll_joint",
]

LEFT_ARM_NAMES = [
    "l_shoulder_pan_joint",
    "l_shoulder_lift_joint",
    "l_upper_arm_roll_joint",
    "l_elbow_flex_joint",
    "l_wrist_roll_joint",
]

LEFT_FINGER_MOTOR = "l_finger_gripper_motor::l_finger"
RIGHT_FINGER_MOTOR = "r_finger_gripper_motor::r_finger"

LEFT_CONTACT_SENSORS = ["l_gripper_l_finger_tip_contact_sensor", "l_gripper_r_finger_tip_contact_sensor"]
RIGHT_CONTACT_SENSORS = ["r_gripper_l_finger_tip_contact_sensor", "r_gripper_r_finger_tip_contact_sensor"]


# ----------------------------------------------------------------------
# Obstacle-avoidance tuning
# ----------------------------------------------------------------------
AVOIDANCE_THRESHOLD = 0.50   # closeness score to start reacting  → ~1.0 m away
STOP_THRESHOLD      = 0.75   # closeness score on BOTH sides → ~0.5 m away (emergency)
STRAFE_DISTANCE     = 0.5    # metres to strafe sideways per avoidance step
STEP_DISTANCE       = 0.5   # metres per forward micro-step
GOAL_TOLERANCE      = 0.30   # metres — stop when this close to goal
HEADING_TOLERANCE   = 0.10   # radians — skip re-orient if error is small
NEAR_GOAL_ZONE      = 1.2    # metres — disable avoidance inside this radius around goal


# ----------------------------------------------------------------------
# Component mapping: low-level robot devices to high-level functional groups
# ----------------------------------------------------------------------
COMPONENT_MAP = {
    "left_wheels": [
        "fl_caster_l_wheel_joint",
        "fr_caster_l_wheel_joint",
        "bl_caster_l_wheel_joint",
        "br_caster_l_wheel_joint"
    ],
    "right_wheels": [
        "fl_caster_r_wheel_joint",
        "fr_caster_r_wheel_joint",
        "bl_caster_r_wheel_joint",
        "br_caster_r_wheel_joint"
    ],
    "left_arm": [
        "l_shoulder_pan_joint",
        "l_shoulder_lift_joint",
        "l_upper_arm_roll_joint",
        "l_elbow_flex_joint",
        "l_wrist_roll_joint"
    ],
    "right_arm": [
        "r_shoulder_pan_joint",
        "r_shoulder_lift_joint",
        "r_upper_arm_roll_joint",
        "r_elbow_flex_joint",
        "r_wrist_roll_joint"
    ],
    "left_gripper": [
        "l_finger_gripper_motor::l_finger",
        "l_gripper_l_finger_tip_contact_sensor",
        "l_gripper_r_finger_tip_contact_sensor"
    ],
    "right_gripper": [
        "r_finger_gripper_motor::r_finger",
        "r_gripper_l_finger_tip_contact_sensor",
        "r_gripper_r_finger_tip_contact_sensor",
    ],
    "torso": ["torso_lift_joint"],
    "head": ["head_tilt_joint"],
    "distance_sensor": ["distance_sensor"]
}
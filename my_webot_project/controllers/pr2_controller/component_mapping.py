# Maps low-level robot components to a high-level functional representation

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
    "head": [
        "head_pan_joint",
        "head_tilt_joint"
    ],
    "torso": ["torso_lift_joint"]
    
}

def map_to_high_level(S_low, component_map):
    S_high = set()

    for comp, devices in component_map.items():
        if any(d in S_low for d in devices):
            S_high.add(comp)

    return S_high
# T - task
# G - goal
# tau - task criticality
# epsilon - goal criticality

# PR2
navigate = {
    "T": {"Navigate_to_box1"},
    "G": {"AvoidCollision"},
    "tau": {
        ("left_wheels", "Navigate_to_box1"): 2,
        ("right_wheels", "Navigate_to_box1"): 2,
        ("left_arm", "Navigate_to_box1"): 1,
        ("left_gripper", "Navigate_to_box1"): 0,
        ("right_arm", "Navigate_to_box1"): 0,
        ("right_gripper", "Navigate_to_box1"): 0,
        ("torso", "Navigate_to_box1"): 0,
        ("head", "Navigate_to_box1"): 0,
    },
    "epsilon": {
        ("left_wheels", "AvoidCollision"): 2,
        ("right_wheels", "AvoidCollision"): 2,
        ("left_arm", "AvoidCollision"): 0,
        ("left_gripper", "AvoidCollision"): 0,
        ("right_arm", "AvoidCollision"): 0,
        ("right_gripper", "AvoidCollision"): 0,
        ("torso", "AvoidCollision"): 0,
        ("head", "AvoidCollision"): 0,
    },
    "kappa": {
        "left_wheels": 0.5,
        "right_wheels": 0.5,
        "left_arm": 0.5,
        "left_gripper": 0.5,
        "right_arm": 0.5,
        "right_gripper": 0.5,
        "torso": 0.5,
        "head": 0.5,

    },
    "waypoints": {
        "box1": None,
        "box2": None,
        "table1": None,
        "table2": None,
    }
}



pickup_object = {
    "T": {"PickupObject"},
    "arm": "left",
    "G": {"GraspStability"},
    "tau": {
        ("left_wheels", "PickupObject"): 2,
        ("right_wheels", "PickupObject"): 2,
        ("left_arm", "PickupObject"): 2,
        ("left_gripper", "PickupObject"): 2,
        ("right_arm", "PickupObject"): 1,
        ("right_gripper", "PickupObject"): 1,
        ("torso", "PickupObject"): 0,
        ("head", "PickupObject"): 0,
    },
    "epsilon": {
        ("left_wheels", "GraspStability"): 2,
        ("right_wheels", "GraspStability"): 2,
        ("left_arm", "GraspStability"): 0,
        ("left_gripper", "GraspStability"): 0,
        ("right_arm", "GraspStability"): 0,
        ("right_gripper", "GraspStability"): 0,
        ("torso", "GraspStability"): 0,
        ("head", "GraspStability"): 0,
    },
    "kappa": {
        "left_wheels": 0.5,
        "right_wheels": 0.5,
        "left_arm": 0.5,
        "left_gripper": 0.5,
        "right_arm": 0.5,
        "right_gripper": 0.5,
        "torso": 0.5,
        "head": 0.5,
    },
    "waypoints": {
        "apple": None,
        "water bottle": None
    }
}

navigagte_and_pickup_object = {
    "T": {"PickupAndDropObject"},
    "arm": "left",
    "G": {"AvoidCollision"},
    "tau": {
        ("left_wheels", "PickupAndDropObject"): 2,
        ("right_wheels", "PPickupAndDropObject"): 2,
        ("left_arm", "PickupAndDropObject"): 2,
        ("left_gripper", "PickupAndDropObject"): 2,
        ("right_arm", "PPickupAndDropObject"): 1,
        ("right_gripper", "PickupAndDropObject"): 1,
        ("torso", "PickupAndDropObject"): 0,
        ("head", "PickupAndDropObject"): 0,
    },
    "epsilon": {
        ("left_wheels", "AvoidCollision"): 2,
        ("right_wheels", "AvoidCollision"): 2,
        ("left_arm", "AvoidCollision"): 0,
        ("left_gripper", "AvoidCollision"): 0,
        ("right_arm", "AvoidCollision"): 0,
        ("right_gripper", "AvoidCollision"): 0,
        ("torso", "AvoidCollision"): 0,
        ("head", "AvoidCollision"): 0,
    },
    "kappa": {
        "left_wheels": 0.5,
        "right_wheels": 0.5,
        "left_arm": 0.5,
        "left_gripper": 0.5,
        "right_arm": 0.5,
        "right_gripper": 0.5,
        "torso": 0.5,
        "head": 0.5,
    },
    "waypoints": {
        "apple": None,
        "water bottle": None,
        "box1": None,
        "box2": None,
        "table1": None,
        "table2": None,
    }
}
import math

# PR2 constants
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

#LEFT_FINGER_SENSOR = "l_finger_gripper_motor::l_finger_sensor"
#RIGHT_FINGER_SENSOR = "r_finger_gripper_motor::r_finger_sensor"

LEFT_CONTACT_SENSORS = ["l_gripper_l_finger_tip_contact_sensor", "l_gripper_r_finger_tip_contact_sensor"]
RIGHT_CONTACT_SENSORS = ["r_gripper_l_finger_tip_contact_sensor", "r_gripper_r_finger_tip_contact_sensor"]

LEFT = "left"
RIGHT = "right"
_gripper_max_torque = {LEFT: None, RIGHT: None}

def almost_equal(a, b):
    return (a < b + TOLERANCE) and (a > b - TOLERANCE)


# '''''''''''''''''''''''''''''
# HELP FUNCTIONS
# '''''''''''''''''''''''''''''
def set_wheels_speeds(supervisor, fll, flr, frl, frr, bll, blr, brl, brr):
    speeds = [fll, flr, frl, frr, bll, blr, brl, brr]
    for i, name in enumerate(WHEEL_NAMES):
        motor = supervisor.getDevice(name)
        motor.setPosition(float('inf')) 
        motor.setVelocity(speeds[i])

def set_wheels_speed(supervisor, speed):
    set_wheels_speeds(supervisor, speed, speed, speed, speed, speed, speed, speed, speed)

def stop_wheels(supervisor):
    set_wheels_speeds(supervisor, 0, 0, 0, 0, 0, 0, 0, 0)


# ''''''''''''''''''''''''''''''''''''''''''''''''''
# ENABLE/DISABLE torques on wheels motors
# ''''''''''''''''''''''''''''''''''''''''''''''''''
def enable_passive_wheels(supervisor, enable):
    for name in WHEEL_NAMES:
        motor = supervisor.getDevice(name)
        if enable:
            motor.setAvailableTorque(0.0)
        else:
            motor.setAvailableTorque(motor.getMaxTorque())

# ''''''''''''''''''''''''''''
# Set rotation wheels angles
# ''''''''''''''''''''''''''''
def set_rotation_wheels_angles(supervisor, fl, fr, bl, br, timestep, wait_on_feedback=True):
    targets = [fl, fr, bl, br]

    if wait_on_feedback:
        stop_wheels(supervisor)
        enable_passive_wheels(supervisor, True)

    for i, name in enumerate(ROTATION_NAMES):
        supervisor.getDevice(name).setPosition(targets[i])

    if wait_on_feedback:
        sensors = [supervisor.getDevice(name + "_sensor") for name in ROTATION_NAMES]
        for sensor in sensors:
            sensor.enable(timestep)

        while supervisor.step(timestep) != -1:
            all_reached = all(
                almost_equal(sensors[i].getValue(), targets[i])
                for i in range(4)
            )
            if all_reached:
                break

        enable_passive_wheels(supervisor, False)


# '''''''''''''''''''''''''''''''''''''''''''
# Apply wheel speed based on resilinece state
# '''''''''''''''''''''''''''''''''''''''''''
def apply_wheel_speeds(supervisor, max_wheel_speed, resilience_manager):

    if resilience_manager:
        effective_state = resilience_manager.get_effective_state()
        for name in WHEEL_NAMES:
            #print(name)
            motor = supervisor.getDevice(name)
            motor.setPosition(float('inf'))
            if name in effective_state:
                motor.setVelocity(0.0)
            else:
                motor.setVelocity(max_wheel_speed)
    else:
        set_wheels_speed(supervisor, max_wheel_speed)



# '''''''''''''''''''''''''''
# Primitive actions 
# '''''''''''''''''''''''''''
def object_grasped(supervisor, arm):
    contact_names = (
        LEFT_CONTACT_SENSORS if arm == "left"
        else RIGHT_CONTACT_SENSORS
    )

    contacts = [supervisor.getDevice(name) for name in contact_names]

    left_contact = contacts[0].getValue()
    right_contact = contacts[1].getValue()

    return left_contact > 0.0 and right_contact > 0.0


# High level function to rotate the robot around itself of a given angle [rad]
def robot_rotate(supervisor, angle, timestep, resilience_check=None, resilience_manager=None, attack_executor=None):
    stop_wheels(supervisor)
    set_rotation_wheels_angles(
        supervisor,
        3.0 * math.pi / 4, math.pi / 4,
        -3.0 * math.pi / 4, -math.pi / 4,
        timestep, wait_on_feedback=True
    )

    max_wheel_speed = MAX_WHEEL_SPEED if angle > 0 else -MAX_WHEEL_SPEED
    set_wheels_speed(supervisor, max_wheel_speed)

    wheel_sensor = supervisor.getDevice("fl_caster_l_wheel_joint_sensor")
    wheel_sensor.enable(timestep)
    supervisor.step(timestep)
    initial_pos = wheel_sensor.getValue()
    expected_distance = abs(angle * 0.5 * (WHEELS_DISTANCE + SUB_WHEELS_DISTANCE))
    braking = False

    while supervisor.step(timestep) != -1:
        if resilience_check:
            resilient = resilience_check()
            if not resilient:
                if resilience_manager and resilience_manager.tick_halt_timer(
                    supervisor.getTime(), resilience_manager.start_time
                ):
                    stop_wheels(supervisor)
                    return "HALTED"

        travel = abs(WHEEL_RADIUS * (wheel_sensor.getValue() - initial_pos))
        if travel > expected_distance:
            break

        if not braking and expected_distance - travel < 0.025:
            max_wheel_speed = 0.1 * max_wheel_speed
            braking = True 

        apply_wheel_speeds(supervisor, max_wheel_speed, resilience_manager)

    set_rotation_wheels_angles(supervisor, 0, 0, 0, 0, timestep, wait_on_feedback=True)
    stop_wheels(supervisor)
    return "DONE"


def robot_go_sideways(supervisor, distance, timestep, resilience_check=None, resilience_manager=None, attack_executor=None):
    """Strafe left (distance > 0) or right (distance < 0) using caster rotation."""
    caster_angle = math.pi / 2 if distance > 0 else -math.pi / 2
    stop_wheels(supervisor)
    set_rotation_wheels_angles(
        supervisor,
        caster_angle, caster_angle, caster_angle, caster_angle,
        timestep, wait_on_feedback=True
    )

    max_wheel_speed = MAX_WHEEL_SPEED if distance > 0 else -MAX_WHEEL_SPEED
    set_wheels_speed(supervisor, max_wheel_speed)

    wheel_sensor = supervisor.getDevice("fl_caster_l_wheel_joint_sensor")
    wheel_sensor.enable(timestep)
    supervisor.step(timestep)
    initial_pos = wheel_sensor.getValue()
    braking = False

    while supervisor.step(timestep) != -1:
        if resilience_check:
            resilient = resilience_check()
            if not resilient:
                if resilience_manager and resilience_manager.tick_halt_timer(
                    supervisor.getTime(), resilience_manager.start_time
                ):
                    stop_wheels(supervisor)
                    set_rotation_wheels_angles(supervisor, 0, 0, 0, 0, timestep, wait_on_feedback=True)
                    return "HALTED"

        travel = abs(WHEEL_RADIUS * (wheel_sensor.getValue() - initial_pos))
        if travel > abs(distance):
            break

        if not braking and abs(distance) - travel < 0.025:
            max_wheel_speed = 0.1 * max_wheel_speed
            braking = True

        apply_wheel_speeds(supervisor, max_wheel_speed, resilience_manager)

    set_rotation_wheels_angles(supervisor, 0, 0, 0, 0, timestep, wait_on_feedback=True)
    stop_wheels(supervisor)
    return "DONE"


def robot_go_forward(supervisor, distance, timestep, resilience_check=None, resilience_manager=None, goal_node=None, attack_executor=None, runtime_check=None):

    max_wheel_speed = MAX_WHEEL_SPEED if distance > 0 else -MAX_WHEEL_SPEED
    set_wheels_speed(supervisor, max_wheel_speed)

    wheel_sensor = supervisor.getDevice("fl_caster_l_wheel_joint_sensor")
    wheel_sensor.enable(timestep)
    supervisor.step(timestep)
    initial_pos = wheel_sensor.getValue()
    braking = False

    while supervisor.step(timestep) != -1:


        if runtime_check:
            if not runtime_check():
                halt_wait = 0.0
                while supervisor.step(timestep) != -1:
                    halt_wait += timestep / 1000.0
                    if halt_wait >= 2:  # 2 seconds delay
                        break
                stop_wheels(supervisor)
                return "HALTED"


        if resilience_check:
            resilient = resilience_check()

            if not resilient:
                if resilience_manager and resilience_manager.tick_halt_timer(
                    supervisor.getTime(), resilience_manager.start_time
                ):
                    stop_wheels(supervisor)
                    return "HALTED"

        # Stop when contact made with goal/object
        if goal_node and len(goal_node.getContactPoints()) > 0:
            stop_wheels(supervisor)
            return "DONE"

        travel = abs(WHEEL_RADIUS * (wheel_sensor.getValue() - initial_pos))
        if travel > abs(distance):
            break
        if not braking and abs(distance) - travel < 0.025:
            max_wheel_speed = 0.1 * max_wheel_speed
            braking = True

        if not (attack_executor and attack_executor.has_active_attacks()):
            apply_wheel_speeds(supervisor, max_wheel_speed, resilience_manager)

    stop_wheels(supervisor)
    return "DONE"


# Set the right/left arm position (forward kinematics)
def set_arm_position(supervisor, arm, shoulder_roll, shoulder_lift, upper_arm_roll, elbow_lift, wrist_roll, timestep, wait_on_feedback=True, speed=0.3):
    names = LEFT_ARM_NAMES if arm == "left" else RIGHT_ARM_NAMES
    targets = [shoulder_roll, shoulder_lift, upper_arm_roll, elbow_lift, wrist_roll]

    for i, name in enumerate(names):
        motor = supervisor.getDevice(name)
        motor.setVelocity(speed)
        motor.setPosition(targets[i])

    if wait_on_feedback:
        sensors = [supervisor.getDevice(name + "_sensor") for name in names]
        for sensor in sensors:
            sensor.enable(timestep)

        while supervisor.step(timestep) != -1:
            if all(almost_equal(sensors[i].getValue(), targets[i]) for i in range(5)):
                break
    
    return "DONE"

# Open or close the gripper.
# If wait_on_feedback is true, the gripper is stopped either when the target is reached,
# or either when something has been gripped
def set_gripper(supervisor, arm, open, torque_when_gripping, timestep, wait_on_feedback=True, speed=0.2):
    global _gripper_max_torque

    side         = arm
    motor_name   = LEFT_FINGER_MOTOR if arm == "left" else RIGHT_FINGER_MOTOR
    contact_names = LEFT_CONTACT_SENSORS if arm == "left" else RIGHT_CONTACT_SENSORS

    motor  = supervisor.getDevice(motor_name)
    sensor = motor.getPositionSensor()
    sensor.enable(timestep)

    contacts = [supervisor.getDevice(name) for name in contact_names]
    for contact in contacts:
        contact.enable(timestep)

    # Ersätter static firstCall + maxTorque
    if _gripper_max_torque[side] is None:
        _gripper_max_torque[side] = motor.getMaxTorque()
    motor.setAvailableTorque(_gripper_max_torque[side])

    if open:
        target = 0.5
        motor.setVelocity(speed)
        motor.setAvailableTorque(_gripper_max_torque[side])
        motor.setPosition(target)
        if wait_on_feedback:
            while supervisor.step(timestep) != -1:
                if almost_equal(sensor.getValue(), target):
                    break
    else:
        target = 0.0
        motor.setVelocity(speed)
        motor.setPosition(target)
        if wait_on_feedback:
            while supervisor.step(timestep) != -1:
                # Vänta tills touch sensors triggar eller target nås
                left_contact  = contacts[0].getValue()
                right_contact = contacts[1].getValue()
                if (left_contact > 0.0 and right_contact > 0.0) or almost_equal(sensor.getValue(), target):
                    break

            current_pos = sensor.getValue()
            motor.setAvailableTorque(torque_when_gripping)
            motor.setPosition(max(0.0, 0.95 * current_pos))
    return "DONE"



import math
import pr2_control as pr2


def move(supervisor, goal_pos, timestep, resilience_check=None, resilience_manager=None, goal_node=None, attack_executor=None):
    robot_pos = supervisor.getSelf().getPosition() # Start position of robot

    dx = goal_pos[0] - robot_pos[0]
    dy = goal_pos[1] - robot_pos[1]
    #print(f'dx = {dx}')
    #print(f'dy = {dy}')
    distance = math.sqrt(dx**2 + dy**2)
    #print(f'Distance {distance}')

    angle_to_target = math.atan2(dy, dx)

    rotation = supervisor.getSelf().getField("rotation").getSFRotation()
    axis_x, axis_y, axis_z, angle = rotation
    robot_angle = angle * axis_z # angle about z-axis to target

    error = angle_to_target - robot_angle
    while error >  math.pi: error -= 2 * math.pi
    while error < -math.pi: error += 2 * math.pi

    #print(f"angle_to_target: {math.degrees(angle_to_target):.1f} deg")
    #print(f"robot_angle:     {math.degrees(robot_angle):.1f} deg")
    #print(f"error:           {math.degrees(error):.1f} deg")

    # Turn towards goal position
    result = pr2.robot_rotate(supervisor, error, timestep, resilience_check, resilience_manager, attack_executor)
    if result == "HALTED":
        return "HALTED"

    # Drive towards goal position
    result = pr2.robot_go_forward(supervisor, distance, timestep, resilience_check, resilience_manager, goal_node, attack_executor)
    if result == "HALTED":
        return "HALTED"

    return result

# ── Composite tasks ────────────────────────────────────────────

def navigate_to_goal(supervisor, waypoints, goal_name, timestep, resilience_check=None, resilience_manager=None, attack_executor=None):
    goal = waypoints[goal_name]
    goal_node = supervisor.getFromDef(goal_name)
    return move(supervisor, goal, timestep, resilience_check, resilience_manager, goal_node, attack_executor)



def pickup_object(supervisor, arm, object_name, timestep, resilience_check=None, resilience_manager=None, attack_executor=None):
    

    # exact pos robot needs to be in (for now)
    # x = -2.83701
    # y = 0.258347

    # joints: 
    # - big rotation inwards(-) and outwards (+) 
    # - shoulder move UP(-) and DOWN (+)
    # - vridning shoulder inwards (-) and outwards(+)
    # - armbåge, endast böjning uppåt (-)
    # - handled, vridning inåt(+) och utåt (-)

    # Set arm above object
    result = pr2.set_arm_position(supervisor, arm, 0.0, 0.0, 0.0, -0.5, 0.0, timestep)
    # goal_drop = [-6.14+0.8, 0.0, 0.0] #table2
    # print(goal_drop[0])

    # open gripper
    result = pr2.set_gripper(supervisor, arm, open=True, torque_when_gripping=0.0, timestep=timestep)

    goal = [-1.38701,0.258347] # Position to pikc up water bottle @ table1
    result = move(supervisor, goal, timestep, resilience_check, resilience_manager, goal_node=None, attack_executor=attack_executor)

    # lower arm towards object (positive shoulder_lift = arm goes down)
    result = pr2.set_arm_position(supervisor, arm, 0.0, 0.1, 0.0, 0.0, 0.0, timestep)

    # Close gripper
    result = pr2.set_gripper(supervisor, arm, open=False, torque_when_gripping=10.0, timestep=timestep)
    
    # Bring arm up
    result = pr2.set_arm_position(supervisor, arm, 0.0, 0.0, 0.0, -0.5, 0.0, timestep)
    
    return result


def navigagte_and_pickup_object(supervisor, waypoints, goal_name, arm, object_name, timestep, resilience_check=None, resilience_manager=None, attack_executor=None):

    # Navigate to object and pick it up
    result = pickup_object(supervisor, arm, object_name, timestep, resilience_check=resilience_check, resilience_manager=resilience_manager, attack_executor=attack_executor)
    if result == "HALTED":
        return "HALTED"

    # Navigate to new position and drop object
    goal = waypoints[goal_name]
    goal_pos = [goal[0] + 0.8, goal[1], goal[2]]    # Stop before table
    result = move(supervisor, goal_pos, timestep, resilience_check, resilience_manager, goal_node=None,attack_executor=attack_executor)
    if result == "HALTED":
        return "HALTED"

    # Lower arm to drop position (same depth as pickup)
    result = pr2.set_arm_position(supervisor, arm, 0.0, 0.1, 0.0, 0.0, 0.0, timestep)

    # Open gripper — bottle fills the full opening so it won't widen further
    result = pr2.set_gripper(supervisor, arm, open=True, torque_when_gripping=0.0, timestep=timestep)

    # Raise arm upward: bottle slides down onto table while gripper lifts clear
    result = pr2.set_arm_position(supervisor, arm, 0.0, 0.0, 0.0, -0.5, 0.0, timestep)

    # Move back away from table
    result = pr2.robot_go_forward(supervisor, -0.5, timestep)

    return "DONE"




    
import rclpy

from controller import Robot
from components.wheel import Wheel
from components.camera import Camera 
from components.distance_sensor import DistanceSensor
from ros2_subscriber import SubscriberNode
from resilience_manager import ResilienceManager
from ids import IDS
from examples import test_example

robot = Robot()
timestep = int(robot.getBasicTimeStep())


'''
# Initialise devices for epuck-robot
left_wheel = Wheel(robot, "left wheel motor")
right_wheel = Wheel(robot, "right wheel motor")
camera = Camera(robot, 'camera', timestep)
distance_sensor = DistanceSensor(robot, "ps0", timestep)
'''

print("Devices in this robot:")

for i in range(robot.getNumberOfDevices()):
    device = robot.getDeviceByIndex(i)
    print("-", device.getName(), "| type:", device.getNodeType())

# ROS init and Node instance
rclpy.init()
sub_node = SubscriberNode()

# Initialise RM
resilience_manager = ResilienceManager()

# Load parameters from test example
G = test_example["G"]
T = test_example["T"]
current_goal = next(iter(G))
current_task = next(iter(T))
tau = test_example["tau"]
epsilon = test_example["epsilon"]
kappa = test_example["kappa"]

# load example to RM
resilience_manager.load_example(tau, epsilon, kappa, current_task, current_goal)

# IDS (get devices defined in RM)
ids = IDS(resilience_manager.D)


# Webot main loop
while robot.step(timestep) != -1:
    
    rclpy.spin_once(sub_node, timeout_sec=0.0)

    # Update IDS
    ids.update_attack_state(sub_node.attack_state)
    ids_output = ids.get_probability_output() 

    # Update S
    resilience_manager.update_compromised_set(ids_output)

    # Check resilience
    resilient = resilience_manager.check_resilience()

    # Log transitions
    resilience_manager.log_state_changes()


    # Apply policy
    velocity = resilience_manager.get_wheel_speed()
    left_wheel.set_speed(velocity)
    right_wheel.set_speed(velocity)


    '''
    if resilience_manager.camera_enabled():
        camera.enable()
    else:
        camera.disable()
    
    if resilience_manager.distance_sensor_enabled():
        distance_sensor.enable()
    else:
        distance_sensor.disable()
    '''

sub_node.destroy_node()
rclpy.shutdown()


from rclpy.node import Node
from my_attack_interfaces.msg import AttackState

# ROS subscriber to attack node
class SubscriberNode(Node):
    def __init__(self):
        super().__init__('subscriber_node')

        self.subscription = self.create_subscription(AttackState, '/attack_state', self.listener_callback, 10)
        self.attack_state = []
        #self.subscription

    def listener_callback(self, msg):
        attacks = []
        for item in msg.compromised_devices:
            component, attack_type = item.split(":")
            attacks.append({"component": component, "type": attack_type})
        self.attack_state = attacks

        #self.get_logger().info("Received attack state")
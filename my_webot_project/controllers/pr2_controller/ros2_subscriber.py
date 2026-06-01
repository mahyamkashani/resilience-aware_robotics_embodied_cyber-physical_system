from rclpy.node import Node
from my_attack_interfaces.msg import AttackState

# ROS subscriber to attack node
class SubscriberNode(Node):
    def __init__(self):
        super().__init__('subscriber_node')

        self.subscription = self.create_subscription(AttackState, '/active_attacks', self.listener_callback, 10)
        self.active_attacks = []
        #self.subscription

    def listener_callback(self, msg):
        attacks = []
        for item in msg.compromised_devices:
            component, attack_type = item.split(":")
            attacks.append({"component": component, "type": attack_type})
        self.active_attacks = attacks

        #self.get_logger().info("Received attack state")
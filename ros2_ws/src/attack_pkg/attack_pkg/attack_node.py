import rclpy
from rclpy.node import Node
from my_attack_interfaces.msg import AttackState

class AttackNode(Node):
    def __init__(self):
        super().__init__('attack_publisher')
        self.attack_publisher = self.create_publisher(AttackState, '/active_attacks', 10)

    '''
    def trigger_attack(self):
        msg = AttackState()
        msg.camera = False
        msg.left_wheel = False
        msg.right_wheel = False
        msg.distance_sensor = False

        self.attack_publisher.publish(msg)
        self.get_logger("Attack started")
        

    def stop_attack(self):
        msg = AttackState()
        msg.camera = False
        msg.left_wheel = False
        msg.right_wheel = False
        msg.distance_sensor = False

        self.attack_publisher.publish(msg)
        self.get_logger().info("Attack stopped")
        '''
    def trigger_attack(self, devices):
        msg = AttackState()
        msg.compromised_devices = devices
        self.attack_publisher.publish(msg)
        self.get_logger("Attack started")
        

    def stop_attack(self):
        msg = AttackState()
        msg.compromised_devices = []
        self.attack_publisher.publish(msg)
        self.get_logger().info("Attack stopped")

def main():
    rclpy.init()
    node = AttackNode()

    try:  
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

if __name__ == '__main__':
    main()

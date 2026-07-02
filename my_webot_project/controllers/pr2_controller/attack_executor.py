'''
GOAL
- Receive attack msg from subscriber node 
- Reason about {component: attack_type}
- Apply attacks
'''

import random

# TODO: add attack on wheels where with different speed
from constants import AttackType, MAX_WHEEL_SPEED, LEFT_FINGER_MOTOR, RIGHT_FINGER_MOTOR # 3.0

class AttackExecutor:

    def __init__(self, supervisor, component_map):
        self.supervisor = supervisor
        self.component_map = component_map
        self.active_attacks = []
        self.random_value = {}

    def update(self, attacks):
        """Ex attack msg: {component: "left_wheels": "type": "STOP"}"""
        self.active_attacks = attacks

    def has_active_attacks(self):
        return len(self.active_attacks) > 0

    def has_active_wheel_attacks(self):
        """True only when a wheel device is under attack (blocks apply_wheel_speeds)."""
        wheel_devices = {"left_wheels", "right_wheels"}
        return any(a["component"] in wheel_devices for a in self.active_attacks)
    
    def neutralized(self, neutralized_devices):
        """Remove attacks that has been mitigated by RM"""
        self.active_attacks = [
            attack for attack in self.active_attacks
            if attack["component"] not in neutralized_devices
        ]

        for comp in neutralized_devices:
            self.random_value.pop(comp, None)


    def apply(self, resilience_manager=None):
        for attack in self.active_attacks:
            self.apply_attack(attack["component"], attack["type"], resilience_manager)

    
    # Attack Types
    def apply_attack(self, component_name, attack_type, resilience_manager=None):
        # Get low level representation
        component = self.component_map.get(component_name, [])


        if attack_type == AttackType.STOP:
            for name in component:
                motor = self.supervisor.getDevice(name)
                if motor and hasattr(motor, 'setPosition'):
                    motor.setPosition(float('inf'))
                    motor.setVelocity(0.0)
        # overspeed
        elif attack_type == AttackType.OVERSPEED:

            if component_name not in self.random_value:
                self.random_value[component_name] = random.choice([
                    1.1, 1.2, 1.3, 1.4, 1.5
                ])

            ran = self.random_value[component_name]

            for name in component:
                motor = self.supervisor.getDevice(name)
                if motor and hasattr(motor, 'setPosition'):
                    motor.setPosition(float('inf'))
                    motor.setVelocity(motor.getMaxVelocity() * ran)

        # underspeed
        elif attack_type == AttackType.UNDERSPEED:

            if component_name not in self.random_value:
                self.random_value[component_name] = 0.6

            ran = self.random_value[component_name]

            for name in component:
                motor = self.supervisor.getDevice(name)
                if motor and hasattr(motor, 'setPosition'):
                    motor.setPosition(float('inf'))
                    motor.setVelocity(motor.getMaxVelocity() * ran)

        # Go backwards
        if attack_type == AttackType.BACKWARD:
            for name in component:
                motor = self.supervisor.getDevice(name)
                if motor and hasattr(motor, 'setPosition'):
                    motor.setPosition(float('inf'))
                    motor.setVelocity(-MAX_WHEEL_SPEED * 0.5)

        # Gripper attacks
        if attack_type == AttackType.GRIP_WEAK:
            # Severity scales with resilience state so physical behaviour matches the formal model
            not_resilient = (
                resilience_manager is not None
                and resilience_manager.current_resilient == "NOT RESILIENT"
            )
            motor_name = (
                LEFT_FINGER_MOTOR if component_name == "left_gripper"
                else RIGHT_FINGER_MOTOR
            )
            if component_name in ("left_gripper", "right_gripper"):
                motor = self.supervisor.getDevice(motor_name)
                if motor:
                    torque = 0.01 if not_resilient else motor.getMaxTorque() * 0.30
                    motor.setAvailableTorque(torque)


'''
        # In progress...
        if attack_type == "GRIP_STRONG":
            """Increase gripper torque to make gripping very strong"""
            if component_name == "left_gripper":
                motor = self.supervisor.getDevice(LEFT_FINGER_MOTOR)
                if motor:
                    max_torque = motor.getMaxTorque()
                    motor.setAvailableTorque(max_torque * 10.0)  # Increase beyond normal
            
            elif component_name == "right_gripper":
                motor = self.supervisor.getDevice(RIGHT_FINGER_MOTOR)
                if motor:
                    max_torque = motor.getMaxTorque()
                    motor.setAvailableTorque(max_torque * 10.0)  # Increase beyond normal
'''

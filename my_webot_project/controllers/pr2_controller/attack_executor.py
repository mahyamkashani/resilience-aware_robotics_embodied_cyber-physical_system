'''
GOAL
- Receive attack msg from subscriber node 
- Reason about {component: attack_type}
- Apply attacks
'''
from pr2_control import MAX_WHEEL_SPEED # 3.0   

class AttackExecutor:

    def __init__(self, supervisor, component_map):
        self.supervisor = supervisor
        self.component_map = component_map
        self.active_attacks = []

    def update(self, attacks):
        """Ex attack msg: {component: "left_wheels": "type": "DOS"}"""
        self.active_attacks = attacks

    def has_active_attacks(self):
        #print("active attacks")
        return len(self.active_attacks) > 0
    
    def neutralized(self, neutralized_devices):
        """Remove attacks that has been mitigated by RM"""
        self.active_attacks = [
            attack for attack in self.active_attacks
            if attack["component"] not in neutralized_devices
        ]


    def apply(self):
        for attack in self.active_attacks:
            self.apply_attack(attack["component"], attack["type"])

    
    # Attack Types
    def apply_attack(self, component, attack_type):
        # low level rep.
        component = self.component_map.get(component, [])


        if attack_type == "STOP":
            for name in component:
                #print(name)
                motor = self.supervisor.getDevice(name)
                if motor:
                    #print(f'settng motor speed')
                    motor.setPosition(float('inf'))
                    motor.setVelocity(0.0)
        # overspeed
        if attack_type == "OVERSPEED":
            for name in component:
                #print(name)
                motor = self.supervisor.getDevice(name)
                if motor:
                    #print(f'settng motor speed')
                    motor.setPosition(float('inf'))
                    motor.setVelocity(MAX_WHEEL_SPEED * 1.5)

        # underspeed
        if attack_type == "UNDERSPEED":
            for name in component:
                #print(name)
                motor = self.supervisor.getDevice(name)
                if motor:
                    #print(f'settng motor speed')
                    motor.setPosition(float('inf'))
                    motor.setVelocity(MAX_WHEEL_SPEED * 0.5)

        # underspeed
        if attack_type == "BACKWARD":
            for name in component:
                #print(name)
                motor = self.supervisor.getDevice(name)
                if motor:
                    #print(f'settng motor speed')
                    motor.setPosition(float('inf'))
                    motor.setVelocity(-MAX_WHEEL_SPEED * 0.5)


        # arm go crazy

        # to much force on gripper

        # ...

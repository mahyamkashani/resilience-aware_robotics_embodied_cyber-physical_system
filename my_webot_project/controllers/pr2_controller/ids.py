'''
Responsibility
- Separate devices into kappa_crit and kappa_base
- Receive attack_state 
- Update and return compromised set S 
- Clear S when device been neutralized
'''
import random
from component_mapping import COMPONENT_MAP

class IDS:

    def __init__(self, D):
        self.D = D
        self.S = set()

        # Task and goal specific criticality values
        self.tau = {}
        self.epsilon = {}
        self.current_task = None
        self.current_goal = None

        # Criticality-based device sets
        self.kappa_crit_set = set()
        self.kappa_base_set = set()

        # Kappa = 1 - detection probability
        self.kappa_crit = 0.0
        self.kappa_base = 0.0

        self.tested_devices = set()

        # Detection delay: steps before a detected attack enters S
        self.detection_delay_steps = 100 # default 0
        self.pending_detection = {}  # comp -> remaining steps

# ------------------------------------------------------------------        
    # Probability that the IDS detects an ongoing attack
    def update_attack_state(self, components):

        for comp in components:
            if comp in self.tested_devices:
                continue 

            #devices = COMPONENT_MAP.get(comp, [])

            is_critical = (
                self.tau.get((comp, self.current_task), 0) == 2 or
                self.epsilon.get((comp, self.current_goal), 0) == 2
            )

            kappa = self.kappa_crit if is_critical else self.kappa_base

            #print(f"[DEBUG] comp={comp} | critical={is_critical} | kappa={kappa}")

            confidence = random.random()
            if confidence >= kappa:
                if self.detection_delay_steps <= 0:
                    #print(f'Adding {comp} to S')
                    self.S.add(comp)
                elif comp not in self.pending_detection:
                    print(f'[IDS] {comp} detected: queued, {self.detection_delay_steps} steps until S')
                    self.pending_detection[comp] = self.detection_delay_steps

            self.tested_devices.add(comp)



    def tick_detection_timer(self):
        ready = [comp for comp, steps in self.pending_detection.items() if steps <= 1]
        for comp in ready:
            del self.pending_detection[comp]
            self.S.add(comp)
            print(f'[IDS] {comp} moved to S after detection delay')
        for comp in self.pending_detection:
            self.pending_detection[comp] -= 1

    # Called when RM neutralizes a component
    def clear_device(self, comp):
        self.tested_devices.discard(comp)
        self.S.discard(comp)
        self.pending_detection.pop(comp, None)
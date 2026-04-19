import random
from component_mapping import COMPONENT_MAP

class IDS:

    def __init__(self, D, detection_probability=1.0):
        self.D_low = D # low level representation of devices
        self.I = {d: 0.0 for d in D}
        self.S = set()
        #self.detection_probability = detection_probability

        self.D_high = {} # high-level representation of devices
        for comp, devices in COMPONENT_MAP.items():
            for d in devices:
                self.D_high[d] = comp
        
        # Task and goal specific criticality values
        self.tau = {}
        self.epsilon = {}
        self.current_task = None
        self.current_goal = None
        
        # Criticality-based device sets
        self.kappa_crit_set = set()
        self.kappa_base_set = set()

        self.kappa_crit = 0.0
        self.kappa_base = 0.0

        # Criticality-based detection probability
        self.detection_probability_crit = 0.9
        self.detection_probability_base = 0.5

    def load_kappa_sets(self, tau, epsilon, current_task, current_goal):
        """Load task/goal specific parameters and build criticality sets"""
        self.tau = tau
        self.epsilon = epsilon
        self.current_task = current_task
        self.current_goal = current_goal

        # Create criticality sets based on tau/epsilon
        self.kappa_crit_set.clear()
        self.kappa_base_set.clear()

        for d in self.D_low:
            #print(f'Prin från load kappa set {d}')

            comp = self.D_high.get(d)

            if comp is None:
                continue

            is_critical = (
                self.tau.get((comp, self.current_task), 0) == 2 or
                self.epsilon.get((comp, self.current_goal), 0) == 2
            )
            
            if is_critical:
                self.kappa_crit_set.add(d)
            else:
                self.kappa_base_set.add(d)
        
        # Print the criticality sets
        #print(f"[IDS] kappa_crit_set: {sorted(self.kappa_crit_set)}")
        #print(f"[IDS] kappa_base_set: {sorted(self.kappa_base_set)}")


    # Probability that the IDS detects an ongoing attack
    def update_attack_state(self, attack_state): 
        components = {attack["component"] for attack in attack_state}
        
        compromised_components = set()
        for comp in components:
            compromised_components.update(COMPONENT_MAP.get(comp, []))

        for d in self.D_low:
            if d in compromised_components:

                if d in self.kappa_crit_set:
                    detected = random.random() < self.detection_probability_crit
                else:
                    detected = random.random() < self.detection_probability_base
                self.I[d] = 1.0 if detected else 0.0 #IDS confidence
            else:
                self.I[d] = 0.0
    

    def get_probability_output(self):
        return self.I.copy()
    

    # ''''''''''''''''''''''''''''''''''''''
    # Compromised devices get added to S
    # ''''''''''''''''''''''''''''''''''''''
    # if we look at crit_set compare with kappa_crit ...
    # return S to controller 
    def update_compromised_set(self):
            self.S.clear()

            for d, confidence in self.I.items():
                if d not in self.D_low:
                    continue
            
                if d in self.kappa_crit_set:
                    kappa = self.kappa_crit
                    is_critical = True
                else:
                    kappa = self.kappa_base
                    is_critical = False

                if confidence >= kappa:
                    self.S.add(d)

                #print(f"[IDS] {d} | critical={is_critical} | I={confidence} | kappa={kappa} | in_S={d in self.S}")

       

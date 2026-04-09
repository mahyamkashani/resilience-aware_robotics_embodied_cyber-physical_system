# TO do: add stochastic probability 

import random
from component_mapping import COMPONENT_MAP

class IDS:

    def __init__(self, D):
        self.D = D
        self.I = {d: 0.0 for d in D}

    def update_attack_state(self, attack_state): 
        components = {attack["component"] for attack in attack_state}
        #detected = random.choice([True,False]) # randomize once for whole msg
        
        compromised_components = set()
        for comp in components:
            compromised_components.update(COMPONENT_MAP.get(comp, []))
        for d in self.D:
            if d in compromised_components:
                #detected = random.choice([True, False])
                self.I[d] = 1.0 #if detected else 0.0
            else:
                self.I[d] = 0.0
    
    def get_probability_output(self):
        return self.I.copy()
from disruption_degradation import degradation, disruption 
from mitigation_feasability import mitigation_feasability
from component_mapping import COMPONENT_MAP

class ResilienceManager:

    def __init__(self, devices):
        self.D = set(devices)     # Component set
        #self.compromised_set = {}


        # Task and goal specific criticality values
        self.tau = {}
        self.epsilon = {}
        self.current_task = {}
        self.current_goal = {}

        # Thresholds
        self.theta_crit = 0.0
        self.theta_base = 0.0
        self.alpha_crit = 0.0
        self.alpha_base = 0.0
        
        # Attack state
        self.S = set() # Compromised set 
        self.mitigatable_devices = set()
        self.active_mitigation = set()
        self.current_resilient = ""
        self.current_attacks = []

        self.normal_speed = 3.0
        self.degraded_speed = 1.0

        self.current_delta = None
        self.current_gamma = None

        # Delay mitigating action when robot under attack (for simulation purposes)
        self.mitigation_delay_steps = 100
        self.mitigation_timer = 0
        self.pending_mitigation = set()

        # Used for logger function
        self.prev_S = set()
        self.prev_resilient = ""
        self.prev_mitigation = set()
        self.prev_delta = None
        self.prev_gamma = None
        self.prev_pending_mitigation = set()
        self.prev_no_mitigation_possible = False
        self.prev_attacks = []


    # '''''''''''''''''''''''''''''''
    # Load example from example.py
    # '''''''''''''''''''''''''''''''
    def load_example(self, tau, epsilon, kappa, current_task, current_goal):
        self.tau = tau
        self.epsilon = epsilon
        # self.kappa = kappa  # Not used anymore
        self.current_task = current_task
        self.current_goal = current_goal

    
    
    
   

    # high level representation of components
    # def update_compromised_set(self, ids_output: dict):
    #     compromised_devices = set()
    #
    #     # 1. samla compromised devices (som nu)
    #     for d, confidence in ids_output.items():
    #         if d not in self.D:
    #             continue
    #
    #     kappa_d = self.compute_kappa(d)
    #
    #     print(f"[DEBUG] Device: {d}, I(d): {confidence}, kappa(d): {kappa_d}")
    #
    #
    #     if confidence >= kappa_d:
    #         compromised_devices.add(d)
    


    # '''''''''''''''''''''''''''''''''''''''
    # Compute effective S (after mitigation)
    # '''''''''''''''''''''''''''''''''''''''
    def get_effective_state(self):
        return self.S - self.active_mitigation
    
    
    # '''''''''''''''''''''''''''''
    # D_available = D - S
    # '''''''''''''''''''''''''''''
    def get_available_devices(self):
        return self.D - self.S
    

    # ''''''''''''''''''''''''''''''''''''''''''''
    # Required Devices D_req to complete task/goal
    # ''''''''''''''''''''''''''''''''''''''''''''
    def get_required_devices(self):
        required = set()

        for d in self.D:
            if (
                self.tau.get((d, self.current_task), 0) > 0
                or
                self.epsilon.get((d, self.current_goal), 0) > 0
            ):
                required.add(d)
        return required

    
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Delay mitigation (Help function to check_resilinece()
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''
    def tick_mitigation_timer(self):
        if self.mitigation_timer <= 0:
            return 
        
        self.mitigation_timer -= 1
        if self.mitigation_timer == 0:
            self.active_mitigation = self.pending_mitigation
            self.pending_mitigation = set()

    
    # '''''''''''''''''''''''''''''
    # Reset all mitigations state
    # '''''''''''''''''''''''''''''
    def reset_mitigation(self):
        self.active_mitigation = set()
        self.pending_mitigation = set()
        self.mitigation_timer = 0


    # '''''''''''''''''''''''''''''''''''
    # Set resilient state and return True
    # ''''''''''''''''''''''''''''''''''''
    def set_resilient(self, delta, gamma):
        self.current_delta = delta
        self.current_gamma = gamma
        self.current_resilient  = "RESILIENT"
        return True
    
    # '''''''''''''''''''''''''''''''''''
    # Set resilient state and return False
    # ''''''''''''''''''''''''''''''''''''
    def set_not_resilient(self, delta, gamma):
        self.current_delta = delta
        self.current_gamma = gamma
        self.current_resilient  = "NOT RESILIENT"
        return False
    


    # ''''''''''''''''''''''''
    # Resilience evalutation
    # ''''''''''''''''''''''''
    def check_resilience(self):

        print(f"[RM] S: {self.S}")
        print(f"[RM] mitigatable: {self.mitigatable_devices}")
        print(f"[RM] intersection: {self.S & self.mitigatable_devices}")

        # No attack
        if not self.S:
            self.reset_mitigation()
            return self.set_resilient(1,1), set()
        
        # Reset mitigation if attack set changed
        if self.active_mitigation and not self.active_mitigation.issubset(self.S):
            self.reset_mitigation()

        # Mitgation delay
        self.tick_mitigation_timer()
        

        # Compute disruption and degradation (without mitigation)
        delta = disruption(self.S, self.tau, self.epsilon, self.current_task, self.current_goal)  
        #print(f"DEBUG disruption: S={self.S}, delta={delta}")
        gamma = degradation(self.S, self.tau, self.epsilon, self.current_task, self.current_goal, self.theta_crit, self.theta_base, self.alpha_crit, self.alpha_base)
                

        # System is resilient (without mitigation)
        if delta == 1 and gamma == 1:
            self.reset_mitigation()
            return self.set_resilient(1,1), set()
        
        # Mitigation is active - evaluate with reduced S
        if self.active_mitigation:
            s_effective = self.get_effective_state()

            delta_eff = disruption(s_effective, self.tau, self.epsilon,self.current_task, self.current_goal)
            gamma_eff = degradation(s_effective, self.tau, self.epsilon,self.current_task, self.current_goal, self.theta_crit, self.theta_base, self.alpha_crit, self.alpha_base)

            if delta_eff == 1 and gamma_eff  == 1:
                return self.set_resilient(delta_eff, gamma_eff), self.active_mitigation
            return self.set_not_resilient(delta_eff, gamma_eff), set()

        
        # Try mitigation feasibility if not resilient
        if not self.pending_mitigation:
            my = mitigation_feasability(self.S, self.tau, self.epsilon, self.current_task, self.current_goal, self.mitigatable_devices, self.theta_crit, self.theta_base, self.alpha_crit, self.alpha_base)

            # If mitigating action exist
            if my["feasible"] == 1:
                self.pending_mitigation = my["neutralized"]
                self.mitigation_timer = self.mitigation_delay_steps

        # No mitigation possible
        return self.set_not_resilient(delta, gamma), set()



    # ''''''''''''''''''''''''''''''''''''''
    # Helper function to log_state_changes()
    # ''''''''''''''''''''''''''''''''''''''
    def is_component_critical(self, component):
        #components = COMPONENT_MAP.get(component, [])
        if(
            self.tau.get((component, self.current_task), 0) > 0
            or
            self.epsilon.get((component, self.current_goal), 0) > 0
        ):
            return True
        return False

    # ''''''''''''''''''''''''
    # Log state transistions
    # ''''''''''''''''''''''''
    def log_state_changes(self):

        # High-level attack logging
        if self.current_attacks != self.prev_attacks:
            for attack in self.current_attacks:
                comp = attack["component"]
                attack_type = attack["type"]

                critical = self.is_component_critical(comp)

                if critical:
                    print(f"[RM] ATTACK: {comp} ({attack_type}) - CRITICAL")
                else:
                    print(f"[RM] ATTACK: {comp} ({attack_type}) - NON-CRITICAL")

            if not self.current_attacks:
                print("[RM] No active attacks")

            self.prev_attacks = list(self.current_attacks)

        if self.S != self.prev_S:
            print(f"[RM] Compromised set updated: {self.S}")
            self.prev_S = self.S.copy()

        # Pending mitigation
        if self.pending_mitigation != self.prev_pending_mitigation:
            if self.pending_mitigation:
                print("[RM] Mitigation pending")
            else:
                print("[RM] Pending mitigation cleared")
            self.prev_pending_mitigation = self.pending_mitigation.copy()

        # Active mitigation
        if self.active_mitigation != self.prev_mitigation:
            if self.active_mitigation:
                print(f"[RM] Active mitigation neutralizing: {self.active_mitigation}")
            else:
                print("[RM] No active mitigation")
            self.prev_mitigation = self.active_mitigation.copy()

        # Resilience state changed
        if self.current_resilient != self.prev_resilient:
            print(f"[RM] Resilience state: {self.current_resilient}")
            self.prev_resilient = self.current_resilient

        # Disruption
        if self.current_delta != self.prev_delta:
            if self.current_delta == 0:
                print("[RM] System disrupted (delta = 0)")
            else:
                print("[RM] Disruption cleared (delta = 1)")
            self.prev_delta = self.current_delta

        # Degradation
        if self.current_gamma != self.prev_gamma:
            if self.current_gamma == 0:
                print("[RM] System degraded beyond tolerance (gamma = 0)")
            else:
                print("[RM] Degradation within tolerance (gamma = 1)")
            self.prev_gamma = self.current_gamma

        # No mitigation possible
        if self.current_resilient == "NOT RESILIENT" \
            and not self.active_mitigation \
            and not self.pending_mitigation:
            if not self.prev_no_mitigation_possible:
                print("[RM] No mitigation possible - system irreparably compromised")
                self.prev_no_mitigation_possible = True
        else:
            self.prev_no_mitigation_possible = False

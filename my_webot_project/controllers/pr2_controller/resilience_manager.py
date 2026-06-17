from disruption_degradation import degradation, disruption, monotonic_degradation
from mitigation_feasability import mitigation_feasability
from component_mapping import COMPONENT_MAP
from logger import log_event

class ResilienceManager:

    def __init__(self, devices):
        self.D = set(devices)     # High level representation

        self.tau = {}
        self.epsilon = {}
        self.current_task = {}
        self.current_goal = {}
        self.theta_crit = 0.0
        self.theta_base = 0.0
        self.alpha_crit = 0.0
        self.alpha_base = 0.0

        self.S = set() # Compromised set 
        self.mitigatable_devices = set()
        self.active_mitigation = set()
        self.current_resilient = ""
        self.current_attacks = []

        self.current_delta = None
        self.current_gamma = None

        # Delay mitigating action when robot under attack (for simulation purposes)
        self.mitigation_delay_steps = 0
        self.mitigation_timer = 0
        self.pending_mitigation = set()

        self.baseline_time = None
        self.start_timer = None
        self.halt_multiplier = 2.0 # halt after 2x baseline

        # Used for logger function
        self.prev_S = set()
        self.prev_resilient = ""
        self.prev_mitigation = set()
        self.prev_delta = None
        self.prev_gamma = None
        self.psi = None
        self.prev_pending_mitigation = set()
        self.prev_no_mitigation_possible = False
        self.prev_attacks = []

        # Live event logging (CSV). Stays disabled unless event_log_path is set.
        self.event_log_path = None
        self.step = 0


    # '''''''''''''''''''''''''''''''
    # Load example from example.py
    # '''''''''''''''''''''''''''''''
    def load_example(self, tau, epsilon, current_task, current_goal):
        self.tau = tau
        self.epsilon = epsilon
        self.current_task = current_task
        self.current_goal = current_goal

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
        if not self.pending_mitigation:
            return
        if self.mitigation_timer <= 0:
            self.active_mitigation = self.pending_mitigation
            self.pending_mitigation = set()
            return
        self.mitigation_timer -= 1
        if self.mitigation_timer == 0:
            self.active_mitigation = self.pending_mitigation
            self.pending_mitigation = set()


    # ''''''''''''''''''''''''''''''''''''''''''''''''''''
    # HALT system if task takes too long
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''
    def tick_halt_timer(self, current_time, start_time):
        if self.baseline_time is None:
            return False
        
        elapsed = current_time - start_time
        halt_threshold = self.baseline_time * self.halt_multiplier

        if self.current_resilient == "NOT RESILIENT" \
            and not self.pending_mitigation \
            and not self.active_mitigation:
            if elapsed >= halt_threshold:
                return True  # HALT
        return False

    
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
        # No attack
        if not self.S:
            self.reset_mitigation()
            return self.set_resilient(1, 1), set()
        
        # Reset mitigation if attack set changed
        if self.active_mitigation and not self.active_mitigation.issubset(self.S):
            self.reset_mitigation()

        # Delay mitigation
        self.tick_mitigation_timer()

        # Evaluate disruption
        delta = disruption(self.S, self.tau, self.epsilon, self.current_task, self.current_goal)

        # Axiom 1: delta = 1 => gamma = 1 (no need to compute gamma)
        # if delta == 1:
            # self.reset_mitigation()
        #     return self.set_resilient(1, 1), set()

        # delta = 0: now evaluate degradation
        gamma = degradation(self.S, self.tau, self.epsilon, self.current_task, self.current_goal, self.theta_crit, self.theta_base, self.alpha_crit, self.alpha_base)

        if delta == 1 and gamma == 1:
            self.reset_mitigation()
            return self.set_resilient(1, 1), set()

        # Case: Mitigation active
        if self.active_mitigation:
            s_effective = self.get_effective_state()

            delta_eff = disruption(s_effective, self.tau, self.epsilon, self.current_task, self.current_goal)

            
            gamma_eff = degradation(s_effective, self.tau, self.epsilon, self.current_task, self.current_goal, self.theta_crit, self.theta_base, self.alpha_crit, self.alpha_base)
            
            if delta_eff == 1 and gamma_eff ==1:
              return self.set_resilient(1, 1), self.active_mitigation
            
            return self.set_not_resilient(delta_eff, gamma_eff), set()

        # Try mitigation
        if not self.pending_mitigation:
            my = mitigation_feasability(self.S, self.tau, self.epsilon, self.current_task, self.current_goal, self.mitigatable_devices, self.theta_crit, self.theta_base, self.alpha_crit, self.alpha_base)

            if my["feasible"] == 1:
                self.pending_mitigation = my["neutralized"]
                self.mitigation_timer = self.mitigation_delay_steps

        # No mitigation possible (Not resilient)
        return self.set_not_resilient(delta, gamma), set()



    # ''''''''''''''''''''''''''''''''''''''
    # Helper function to log_state_changes()
    # ''''''''''''''''''''''''''''''''''''''
    def is_component_critical(self, component):
        #components = COMPONENT_MAP.get(component, [])
        if(
            self.tau.get((component, self.current_task), 0) > 1
            or
            self.epsilon.get((component, self.current_goal), 0) > 1
        ):
            return True
        return False

    # ''''''''''''''''''''''''
    # Log state transistions
    # ''''''''''''''''''''''''
    def log_state_changes(self, current_time=None):

        changed = False  # set True by any transition below -> triggers a CSV row

        # High-level attack logging
        if self.current_attacks != self.prev_attacks:
            for attack in self.current_attacks:
                comp = attack["component"]
                attack_type = attack["type"]
                critical = self.is_component_critical(comp)
                if critical:
                    print(f"ATTACK: {comp} ({attack_type}) - CRITICAL")
                else:
                    print(f"ATTACK: {comp} ({attack_type}) - NON-CRITICAL")
            self.prev_attacks = list(self.current_attacks)
            changed = True

        # Active mitigation
        if self.active_mitigation != self.prev_mitigation:
            if self.active_mitigation:
                print(f"[RM] Active mitigation neutralizing: {self.active_mitigation}")
            self.prev_mitigation = self.active_mitigation.copy()
            changed = True

        # Compromised set
        if self.S != self.prev_S:
            print(f"[RM] Compromised set S updated: {self.S}")
            self.prev_S = self.S.copy()
            changed = True

        # Disruption
        if self.current_delta != self.prev_delta:
            if self.current_delta == 0:
                print("[RM] System disrupted → δ = 0")
            else:
                print("[RM] System not disrupted → δ = 1")
            self.prev_delta = self.current_delta
            changed = True

            # Axiom 1: delta = 0 -> alltid logga gamma
            # if self.current_delta == 0:
            #    self.prev_gamma = None  # tvinga gamma-blocket att trigga

        # Degradation (loggas alltid när delta = 0 och ändras)
        if self.current_gamma != self.prev_gamma:
            if self.current_gamma == 0:
                self.psi = monotonic_degradation(
                    self.S,
                    self.tau,
                    self.epsilon,
                    self.current_task,
                    self.current_goal,
                    self.alpha_crit,
                    self.alpha_base
                )
                print(f"[RM] System degraded beyond tolerance: ψ={self.psi:.1f} < θ={self.theta_crit:.1f} → γ = {self.current_gamma}")
            else:
                print("[RM] Degradation within tolerance → γ = 1")
            self.prev_gamma = self.current_gamma
            changed = True

        # Resilience state
        if self.current_resilient != self.prev_resilient:
            print(f"[RM] Resilience state: {self.current_resilient}")
            self.prev_resilient = self.current_resilient
            changed = True

        # Pending mitigation
        if self.pending_mitigation != self.prev_pending_mitigation:
            if self.pending_mitigation:
                print("[RM] Mitigation pending")
            self.prev_pending_mitigation = self.pending_mitigation.copy()
            changed = True

        # No mitigation possible
        if self.current_resilient == "NOT RESILIENT" \
            and not self.active_mitigation \
            and not self.pending_mitigation:
            if not self.prev_no_mitigation_possible:
                print("[RM] No mitigation possible - system irreparably compromised")
                self.prev_no_mitigation_possible = True
                changed = True
        else:
            self.prev_no_mitigation_possible = False

        # Append a CSV row capturing the attack -> mitigation -> resilience flow
        if changed and self.event_log_path:
            self._log_event_row(current_time)

    # ''''''''''''''''''''''''''''''''''''''''
    # Append one snapshot row to the event CSV
    # ''''''''''''''''''''''''''''''''''''''''
    def _log_event_row(self, current_time):
        self.step += 1
        psi = monotonic_degradation(
            self.S, self.tau, self.epsilon,
            self.current_task, self.current_goal,
            self.alpha_crit, self.alpha_base,
        )

        def fmt_set(s):
            return "{" + ",".join(sorted(s)) + "}"

        log_event(self.event_log_path, {
            "time": round(current_time, 2) if current_time is not None else "",
            "step": self.step,
            "attacks": ";".join(f'{a["component"]}:{a["type"]}' for a in self.current_attacks),
            "S": fmt_set(self.S),
            "delta": self.current_delta,
            "gamma": self.current_gamma,
            "psi": round(psi, 3),
            "resilient": self.current_resilient,
            "pending_mitigation": fmt_set(self.pending_mitigation),
            "active_mitigation": fmt_set(self.active_mitigation),
        })
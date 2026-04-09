from dispruption_degradation import degradation, disruption 
from mitigation_feasability import mitigation_feasability

class ResilienceManager:

    def __init__(self):

        # Component set
        self.D = {
            "camera", 
            "left_wheel", 
            "right_wheel", 
            "distance_sensor"
            } 
        
        self.kappa = {
            "camera": 0.5,
            "left_wheel": 0.5,
            "right_wheel": 0.5,
            "distance_sensor": 0.5
        }

        self.tau = {}
        self.epsilon = {}
        #self.kappa = {}
        self.current_task = {}
        self.current_goal = {}

        self.S = set() # Compromised set 
        self.active_mitigation = set()
        self.current_resilient = None

        self.normal_speed = 5.0
        self.degraded_speed = 1.0

        # Used for logger function
        self.prev_S = set()
        self.prev_resilient = None
        self.prev_mitigation = set()

        

    def load_example(self, tau, epsilon, kappa, current_task, current_goal):
        self.tau = tau
        self.epsilon = epsilon
        self.kappa = kappa
        self.current_task = current_task
        self.current_goal = current_goal

    
    def update_compromised_set(self, ids_output: dict):
        self.S.clear()

        for d, confidence in ids_output.items():
            if d in self.D and confidence > self.kappa[d]:
                self.S.add(d)

    # Compute effective S (after mitigation)
    def get_effective_state(self):
        return self.S - self.active_mitigation
    
    # D_available = D - D_req - S
    def get_available_devices(self):
        return self.D - self.S
    

    # Required Devices D_req to complete task/goal
    def get_required_devices(self):
        required = set()

        for d in self.D:
            if (
                self.tau.get((d, self-self.current_task), 0) > 0
                or
                self.epsilon.get((d, self.current_goal, 0)) > 0
            ):
                required.add(d)
        return required

    # Resilience evalutation
    def check_resilience(self):

        if not self.S:
            self.active_mitigation = set()
            self.current_resilient = True
            return True

        delta = disruption(self.S, 
                           self.tau, 
                           self.epsilon, 
                           self.current_task, 
                           self.current_goal
                           )
        
        gamma = degradation(self.S, 
                            self.tau, 
                            self.epsilon, 
                            self.current_task, 
                            self.current_goal
                            )

        # System is resilient
        if delta == 1 and gamma == 1:
            self.active_mitigation = set()
            self.current_resilient = True
            return True
        
        # Try mitigation feasibility
        my = mitigation_feasability(self.S, 
                                    self.tau, 
                                    self.epsilon, 
                                    self.current_task, 
                                    self.current_goal
                                    )
        
        if my["feasible"] == 1:
            if self.active_mitigation != my["neutralized"]:
                self.active_mitigation = my['neutralized']
            self.current_resilient = True
            return True
        
        # No mitigation possible
        self.active_mitigation = set()
        self.current_resilient = False
        return False


    # Log state transistions
    def log_state_changes(self):
        if self.S != self.prev_S:
            print(f"[RM] Compromised set updated: {self.S}")
            self.prev_S = self.S.copy()

        # Log resilience
        if self.active_mitigation != self.prev_mitigation:
            if self.active_mitigation:
                print(f"[RM] Active mitigation neutralizing: {self.active_mitigation}")
            else:
                print("[RM] No active mitigation")
            self.prev_mitigation = self.active_mitigation.copy()

        # Resilience state changed
        if self.current_resilient != self.prev_resilient:
            print("current:", self.current_resilient, "prev:", self.prev_resilient)
            print(f"[RM] Resilience state changed: {self.current_resilient}")
            self.prev_resilient = self.current_resilient

    
    # Policy
    def get_wheel_speed(self):
        if not self.current_resilient:
            return self.degraded_speed
        return self.normal_speed
        


    '''
    def camera_enabled(self):
        return "camera" not in self.S
    
    def distance_sensor_enabled(self):
        return "distance_sensor" not in self.S
    '''

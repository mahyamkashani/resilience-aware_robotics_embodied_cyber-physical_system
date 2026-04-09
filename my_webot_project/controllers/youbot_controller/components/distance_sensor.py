class DistanceSensor:
    def __init__(self, robot, name, timestep):
        self.sensor = robot.getDevice(name)
        self.timestep = timestep
        self.enabled = False
    
    def enable(self):
        if not self.enabled:
            self.sensor.enable(self.timestep)
            self.enabled = True
    

    def disable(self):
        if self.enabled:
            self.sensor.disable()
            self.enabled = False
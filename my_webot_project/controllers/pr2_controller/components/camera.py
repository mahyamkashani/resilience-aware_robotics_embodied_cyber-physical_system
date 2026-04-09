class Camera:
    def __init__(self, robot, name, timestep):
        self.camera = robot.getDevice(name)
        self.timestep = timestep
        self.enabled = False
    
    # Turn camera ON/OFF
    def enable(self):
        if not self.enabled:
            self.camera.enable(self.timestep)
            self.enabled = True
    

    def disable(self):
        if self.enabled:
            self.camera.disable()
            self.enabled = False

    def is_enabled(self):
        return self.camera.getSamplingPeriod() > 0
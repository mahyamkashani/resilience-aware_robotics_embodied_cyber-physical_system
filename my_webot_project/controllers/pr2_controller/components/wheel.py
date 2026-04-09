class Wheel:
    def __init__(self, robot, name):
        self.motor = robot.getDevice(name)
        self.motor.setPosition(float('inf'))
        self.motor.setVelocity(0.0)
        

    def set_speed(self, speed):
        self.motor.setVelocity(speed)
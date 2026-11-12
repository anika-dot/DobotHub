'''
Dobot API with core functionality for the Dobot Magician robot.
Everything that needs to be sent to the robot is done through this API.

robot.move_to(...)
robot.get_pose()
robot.home()

robot.gripper(...)
robot.suction(...)
robot.conveyor(...)

robot.get_ir()
robot.get_color()

robot.set_io(...)
robot.get_io(...)

robot.get_alarms()
...

'''

from time import sleep, time

from .client import Client


class Dobot:
    """
    Dobot API with core functionality for the Dobot Magician robot.
    """
    def __init__(self, port):
        self.client = Client(port)

        self.client.stop_queue(True)
        self.client.clear_queue()
        self.client.start_queue()

        self.client.set_point_to_point_jump_params(10, 10)
        self.client.set_point_to_point_joint_params([100, 100, 100, 100], [100, 100, 100, 100]) # Geändert von 50 auf 100
        self.client.set_point_to_point_coordinate_params(100, 100, 100, 100) # Geändert von 50 auf 100
        self.client.set_point_to_point_common_params(100, 100) # Geändert von 50 auf 100
        self.client.set_point_to_point_jump2_params(5, 5, 5)

        self.client.set_jog_joint_params([50, 50, 50, 50], [50, 50, 50, 50]) # in client.py marked as "does not work"
        self.client.set_jog_coordinate_params([50, 50, 50, 50], [50, 50, 50, 50]) # in client.py marked as "does not work"
        self.client.set_jog_common_params(50, 50)

        self.client.set_continous_trajectory_params(50, 50, 50)

    def connected(self):
        """
        Returns True if the Dobot is connected.
        """
        return self.client.connected()

    def get_pose(self):
        """
        Returns the current pose of the Dobot as a tuple (x, y, z, r, joint1, joint2, joint3, joint4).
        """
        return self.client.get_pose()

    def home(self, wait=True):
        """
        Move the Dobot to the home position.
        """
        self.client.set_homing_command(0)
        if wait:
            self.wait()

    def move_to(self, x, y, z, r, mode=3, wait=True):
        """
        Move to the absolute coordinate, one axis at a time.
        TO CHECK (see interface in notebook)
        """
        self.client.set_point_to_point_command(mode, x, y, z, r)
        if wait:
            self.wait()

    def slide_to(self, x, y, z, r, wait=True):
        """ 
        Slide to the absolute coordinate, shortest possible path.
        TO CHECK (see interface in notebook)
        """
        self.client.set_point_to_point_command(4, x, y, z, r)
        if wait:
            self.wait()

    def move_to_relative(self, x, y, z, r, wait=True):
        """
        Move to the relative coordinate, one axis at a time.
        TO CHECK (see interface in notebook)
        """
        self.client.set_point_to_point_command(7, x, y, z, r)
        if wait:
            self.wait()

    def slide_to_relative(self, x, y, z, r, wait=True):
        """
        Slide to the relative coordinate, one axis at a time.
        TO CHECK (see interface in notebook)
        """
        self.client.set_point_to_point_command(6, x, y, z, r)
        if wait:
            self.wait()

    def wait(self, queue_index=None):
        """
        Wait until the instruction finishes.
        If queue_index is None, wait until the current instruction finishes.
        If queue_index is given, wait until the instruction with that index finishes.
        Use a zero wait as a non-operation to bypass the limitation
        """
        self.client.wait(0)

        if queue_index is None:
            queue_index = self.client.get_current_queue_index()
        while True:
            if self.client.get_current_queue_index() > queue_index:
                break

            sleep(0.5)

    def follow_path(self, path, wait=True):
        """
        Move according to the given path, which is a list of points [(x1, y1, z1), (x2, y2, z2), ...].
        The points are absolute coordinates.
        """
        self.client.stop_queue()
        queue_index = None
        for point in path:
            queue_index = self.client.set_continous_trajectory_command(1, point[0], point[1], point[2], 50)
        self.client.start_queue()
        if wait:
            self.wait(queue_index)

    def follow_path_relative(self, path, wait=True):
        """
        Move according to the given path, which is a list of points [(dx1, dy1, dz1), (dx2, dy2, dz2), ...].
        The points are relative coordinates.
        """
        self.client.stop_queue()
        queue_index = None
        for point in path:
            queue_index = self.client.set_continous_trajectory_command(0,  point[0], point[1], point[2], 50)
        self.client.start_queue()
        if wait:
            self.wait(queue_index)


#### Added.
# ----- Speed -----
    def speed(self, velocity=100, acceleration=100):
        """
        Set the movement speed and acceleration.
        velocity, acceleration: ratio in percent (common) and mm/s, mm/s² (coordinate)
        """
        self.client.set_point_to_point_common_params(velocity, acceleration)
        self.client.set_point_to_point_coordinate_params(velocity, velocity, acceleration, acceleration)

# ----- Gripper -----
    def gripper_open(self, wait=True, delay=500):
        """
        Open the gripper.
        """
        self.client.set_end_effector_gripper(True, False)
        self._effector_wait(wait, delay)

    def gripper_close(self, wait=True, delay=500):
        """
        Close the gripper.
        """
        self.client.set_end_effector_gripper(True, True)
        self._effector_wait(wait, delay)

    def gripper_idle(self, wait=True):
        """
        Switch off the gripper pump (gripper becomes loose).
        """
        self.client.set_end_effector_gripper(False, False)
        if wait:
            self.wait()

# ----- Suction Cup -----
    def suction_on(self, wait=True, delay=500):
        """
        Switch on the suction cup (grabs the object)."""
        self.client.set_end_effector_suction_cup(True, True)
        self._effector_wait(wait, delay)

    def suction_off(self, wait=True, delay=500):
        """
        Switch off the suction cup (releases the object)."""
        self.client.set_end_effector_suction_cup(False, False)
        self._effector_wait(wait, delay)

    def _effector_wait(self, wait, delay):
        """
        Wait for the pneumatic effectors to finish their action. Queue a pause so the next movement waits for it.
        """
        if delay > 0:
            self.client.wait(delay)
        if wait:
            self.wait()


# Sensor ports on the Dobot Magician base
GP1, GP2, GP4, GP5 = 0, 1, 2, 3

# ----- Conveyor belt -----
def conveyor(self, speed, index=0):
    """
    Run the conveyor belt at the given speed in mm/s (negative = reverse).
    """
    self.client.set_conveyor_speed(speed, index)

def conveyor_stop(self, index=0):
    """
    Stop the conveyor belt.
    """
    self.client.set_conveyor_speed(0, index)

def conveyor_distance(self, distance, speed=50, index=0):
    """
    Move the belt by a distance in mm. Blocks until done (host-side timing).
    """
    self.conveyor(speed if distance >= 0 else -speed, index)
    sleep(abs(distance) / speed)
    self.conveyor_stop(index)

# ----- IR sensor (light barrier) -----
def ir_enable(self, port=GP4, enable=True):
    """
    Enable or disable the IR sensor (light barrier) on the given port.
    """
    self.client.set_ir_switch(0, int(enable), port, 1)  # version 1 = sensor V2

def get_ir(self, port=GP4):
    """
    Returns True if the IR sensor (light barrier) on the given port detects an object.
    """
    return self.client.get_ir_state(port)

def wait_for_object(self, port=GP4, timeout=None):
    """
    Block until the light barrier detects an object. Returns False on timeout.
    """
    start = time()
    while not self.get_ir(port):
        if timeout is not None and time() - start > timeout:
            return False
        sleep(0.05)
    return True

# ----- Color sensor -----
def color_enable(self, port=GP2, enable=True):
    """
    Enable or disable the color sensor on the given port."""
    self.client.set_color_sensor(0, int(enable), port, 1)

def get_color(self):
    """
    Returns (r, g, b) as detected by the color sensor.
    """
    return self.client.get_color_sensor(0)




# ----- Shutdown -----
def close(self):
    """
    Stop all motion and close the connection to the Dobot.
    """
    self.conveyor_stop()
    self.client.set_end_effector_gripper(False, False)
    self.client.set_end_effector_suction_cup(False, False)
    self.client.close()

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

from .client import Client


class Dobot:
    '''
    Control a Dobot robot.
    '''

    def __init__(self, port):
        self.client = Client(port)

    

    def connect(self):
        """
        Connect to the Dobot robot.
        """
        self.client.connect()

    def disconnect(self):
        """
        Disconnect from the Dobot robot.
        """
        self.client.disconnect()

    def move_to(
        self,
        x: float,
        y: float,
        z: float,
        r: float,
        *,
        mode: PTPMode = PTPMode.MOVL_XYZ,
        wait: bool = True,
    ) -> None:
        self.client.move_to(
            x=x,
            y=y,
            z=z,
            r=r,
            mode=mode,
            wait=wait,
        )

    def get_pose(self) -> Pose:
        """
        Get the current pose of the Dobot robot.
        """
        return self.client.get_pose()

    def home(self) -> None:
        """
        Move the Dobot robot to the home position.
        """
        self.client.home()

    def gripper_open(self) -> None:
        self.client.gripper_open()

    def gripper_close(self) -> None:
        self.client.gripper_close()

    def get_ir(self) -> bool:
        return self.client.get_ir()

    def get_color(self):
        return self.client.get_color()

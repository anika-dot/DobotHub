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



class Dobot:
    '''
    Control a Dobot robot.
    '''


    def __init__(
        self,
        port: str,
        *,
        baudrate: int = 115200,
        timeout: float = 1.0,
    ) -> None:
        self._protocol = DobotProtocol(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
        )

    def connect(self) -> None:
        self._protocol.connect()

    def disconnect(self) -> None:
        self._protocol.disconnect()

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
        self._protocol.move_to(
            x=x,
            y=y,
            z=z,
            r=r,
            mode=mode,
            wait=wait,
        )

    def get_pose(self) -> Pose:
        return self._protocol.get_pose()

    def home(self) -> None:
        self._protocol.home()

    def gripper_open(self) -> None:
        self._protocol.gripper_open()

    def gripper_close(self) -> None:
        self._protocol.gripper_close()

    def get_ir(self) -> bool:
        return self._protocol.get_ir()

    def get_color(self):
        return self._protocol.get_color()
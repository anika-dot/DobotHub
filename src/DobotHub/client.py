'''
Protocol module for communication with the Dobot.

Message
Command
checksum
encode
decode
parse
...

'''

class Client:

    def __init__(
        self,
        port: str,
        baudrate: int,
        timeout: float,
    ):
        self._serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
        )

    def connect(self):
        if not self._serial.is_open:
            self._serial.open()

    def disconnect(self):
        if self._serial.is_open:
            self._serial.close()

    def get_pose(self):
        # Implementation for getting the robot's pose
        pass

    def move_to(self, x, y, z, r, mode, wait):
        # Implementation for moving the robot to a specific position
        pass

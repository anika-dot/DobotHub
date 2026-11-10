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

import serial
import threading # threading is needed for the client to handle multiple incoming messages

class Client:

    def __init__(self, port):
        self._serial = serial.Serial(port=port,baudrate=115200,timeout=1,)
        self._lock = threading.Lock()  # Lock for thread-safe operations

    def send(self, message):
        """
        Send a message to the Dobot robot.
        """
        self._serial.write(message.encode())
        
    def connect(self):
        """
        Connect to the Dobot robot.
        """
        if not self._serial.is_open:
            self._serial.open()

    def disconnect(self):
        """
        Disconnect from the Dobot robot.
        """
        if self._serial.is_open:
            self._serial.close()

### Movement Commands
    def get_pose(self):
        """
        Get the current pose of the Dobot robot.
        """
        # Implementation for getting the robot's pose
        pass

    def home(self):
        """
        Move the Dobot robot to its home position.
        Message ID: 31
        """
        request = Message(
            header=[0xAA, 0xAA],
            length=2,
            id=31,
            rw=True,
            is_queued=True,
            params=[0x00],
            direction='out'
        )
        return self.send(request)
    
        


    def move_to(self, x, y, z, r, mode, wait):
        """
        Move the Dobot robot to a specific position.
        """
        # Implementation for moving the robot to a specific position
        pass

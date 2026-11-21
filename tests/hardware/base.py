"""
Basis for hardware tests.

All hardware tests share ONE connection to the Dobot (setup including queue reset takes time
and the COM port cannot be reopened arbitrarily fast under Windows).

The connection is closed at the end of the pytest session in conftest.py.

Port order: --port  >  Environment variable DOBOT_PORT  >  find_port()
"""

import unittest

from DobotHub.dobot import Dobot, find_port
from DobotHub.types import MODE_PTP

PORT = None          # is set in conftest.pytest_configure
_bot = None

# Safe positions within the work area (mm). Adjust to your own setup!
SAFE_POINT = (200.0, 0.0, 50.0, 0.0)
SAFE_POINT_2 = (220.0, 40.0, 60.0, 0.0)

POSITION_TOLERANCE = 2.0   # mm
ANGLE_TOLERANCE = 1.0      # Degree


def connect():
    """
    Connects to the Dobot and returns a Dobot instance. 
    If already connected, returns the existing instance.
    """
    global _bot
    if _bot is None:
        _bot = Dobot(PORT or find_port())
    return _bot


def disconnect():
    """
    Disconnects from the Dobot and closes the connection.
    """
    global _bot
    if _bot is not None:
        try:
            _bot.close()
        finally:
            _bot = None


class HardwareTestCase(unittest.TestCase):
    """
    Base class for hardware tests. Provides `self.bot` (Dobot) and `self.client` (Client).
    """

    @classmethod
    def setUpClass(cls):
        cls.bot = connect()
        cls.client = cls.bot.client

    # --- Helper functions
    def go_safe(self, point=SAFE_POINT):
        """
        Drives the robot to a safe position in Cartesian mode.
        """
        self.bot.move_to(*point, mode=MODE_PTP.MOVJ_XYZ)

    def assertPositionAlmostEqual(self, actual, expected, delta=POSITION_TOLERANCE):
        """
        Compares (x, y, z) with tolerance.
        """
        for name, a, e in zip("xyzr", actual, expected):
            self.assertAlmostEqual(a, e, delta=delta, msg=f"axis {name}: {a:.2f} != {e:.2f}")

"""
Basis für Hardware-Tests.

Alle Hardware-Tests teilen sich EINE Verbindung zum Dobot (Aufbau inkl. Queue-Reset dauert
und der COM-Port lässt sich unter Windows nicht beliebig schnell neu öffnen).
Die Verbindung wird am Ende der pytest-Session in conftest.py geschlossen.

Port-Reihenfolge: --port  >  Umgebungsvariable DOBOT_PORT  >  find_port() (Auto-Erkennung per USB-VID)
"""

import unittest

from DobotHub.dobot import Dobot, find_port
from DobotHub.types import MODE_PTP

PORT = None          # wird in conftest.pytest_configure gesetzt
_bot = None

# Sichere Positionen im Arbeitsbereich (mm). An den eigenen Aufbau anpassen!
SAFE_POINT = (200.0, 0.0, 50.0, 0.0)
SAFE_POINT_2 = (220.0, 40.0, 60.0, 0.0)

POSITION_TOLERANCE = 2.0   # mm
ANGLE_TOLERANCE = 1.0      # Grad


def connect():
    global _bot
    if _bot is None:
        _bot = Dobot(PORT or find_port())
    return _bot


def disconnect():
    global _bot
    if _bot is not None:
        try:
            _bot.close()
        finally:
            _bot = None


class HardwareTestCase(unittest.TestCase):
    """Basisklasse: stellt `self.bot` (Dobot) und `self.client` (Client) bereit."""

    @classmethod
    def setUpClass(cls):
        cls.bot = connect()
        cls.client = cls.bot.client

    # --- Hilfsfunktionen ---
    def go_safe(self, point=SAFE_POINT):
        """Fährt eine sichere Position im kartesischen Modus an."""
        self.bot.move_to(*point, mode=MODE_PTP.MOVJ_XYZ)

    def assertPositionAlmostEqual(self, actual, expected, delta=POSITION_TOLERANCE):
        """Vergleicht (x, y, z, r) mit Toleranz."""
        for name, a, e in zip("xyzr", actual, expected):
            self.assertAlmostEqual(a, e, delta=delta, msg=f"Achse {name}: {a:.2f} != {e:.2f}")

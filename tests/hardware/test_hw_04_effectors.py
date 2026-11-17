"""
Hardware-Tests Stufe 4: Endeffektoren (Greifer, Saugnapf, Laser).

Jeder Test hat einen eigenen Marker. Nur das montierte Werkzeug testen, z. B.:
    pytest --dobot -m gripper
    pytest --dobot -m "hardware and not laser and not suction"

Die Rücklese-Tests prüfen auch den Getter-Parser für ID 61-63 (x[1] == 2 in parser.py),
dessen Format in den Unit-Tests nicht geklärt werden konnte.
"""

import unittest

import pytest

from tests.hardware.base import HardwareTestCase


@pytest.mark.gripper
class TestGripper(HardwareTestCase):
    def tearDown(self):
        self.bot.gripper_idle()

    def test_open(self):
        self.bot.gripper_open()
        self.assertEqual(self.client.get_end_effector_gripper(), (True, False))

    def test_close(self):
        self.bot.gripper_close()
        self.assertEqual(self.client.get_end_effector_gripper(), (True, True))

    def test_idle(self):
        self.bot.gripper_close()
        self.bot.gripper_idle()
        self.assertEqual(self.client.get_end_effector_gripper(), (False, False))


@pytest.mark.suction
class TestSuctionCup(HardwareTestCase):
    def tearDown(self):
        self.bot.suction_off()

    def test_on(self):
        self.bot.suction_on()
        self.assertEqual(self.client.get_end_effector_suction_cup(), (True, True))

    def test_off(self):
        self.bot.suction_on()
        self.bot.suction_off()
        self.assertEqual(self.client.get_end_effector_suction_cup(), (False, False))


@pytest.mark.laser
class TestLaser(HardwareTestCase):
    def tearDown(self):
        self.bot.laser(False)

    def test_on(self):
        self.bot.laser(True)
        self.assertEqual(self.client.get_end_effector_laser(), (True, True))

    def test_off(self):
        self.bot.laser(True)
        self.bot.laser(False)
        self.assertEqual(self.client.get_end_effector_laser(), (True, False))


if __name__ == "__main__":
    unittest.main()

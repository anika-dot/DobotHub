"""
Hardware-tests for DobotHub.
Step 4: end effectors (gripper, suction cup, laser).

Every class has its own marker. Only test the mounted tool, e.g.:
    pytest --dobot -m gripper
    pytest --dobot -m "hardware and not laser and not suction"

The read-back tests also check the getter parser for IDs 61-63 (x[1] == 2 in parser.py),
whose format could not be clarified in the unit tests.
"""

import unittest

import pytest

from tests.hardware.base import HardwareTestCase


@pytest.mark.gripper
class TestGripper(HardwareTestCase):
    """Pneumatic gripper."""

    def tearDown(self):
        """Switches the gripper pump off after each test."""
        self.bot.gripper_idle()

    def test_open(self):
        """gripper_open() reports control on, grip off."""
        self.bot.gripper_open()
        self.assertEqual(self.client.get_end_effector_gripper(), (True, False))

    def test_close(self):
        """gripper_close() reports control on, grip on."""
        self.bot.gripper_close()
        self.assertEqual(self.client.get_end_effector_gripper(), (True, True))

    def test_idle(self):
        """gripper_idle() reports control off, grip off."""
        self.bot.gripper_close()
        self.bot.gripper_idle()
        self.assertEqual(self.client.get_end_effector_gripper(), (False, False))


@pytest.mark.suction
class TestSuctionCup(HardwareTestCase):
    """Suction cup."""

    def tearDown(self):
        """Switches the suction off after each test."""
        self.bot.suction_off()

    def test_on(self):
        """suction_on() reports control on, suction on."""
        self.bot.suction_on()
        self.assertEqual(self.client.get_end_effector_suction_cup(), (True, True))

    def test_off(self):
        """suction_off() reports control off, suction off."""
        self.bot.suction_on()
        self.bot.suction_off()
        self.assertEqual(self.client.get_end_effector_suction_cup(), (False, False))


@pytest.mark.laser
class TestLaser(HardwareTestCase):
    """Laser engraver."""

    def tearDown(self):
        """Switches the laser off after each test."""
        self.bot.laser(False)

    def test_on(self):
        """laser(True) reports control on, laser on."""
        self.bot.laser(True)
        self.assertEqual(self.client.get_end_effector_laser(), (True, True))

    def test_off(self):
        """laser(False) reports control on, laser off."""
        self.bot.laser(True)
        self.bot.laser(False)
        self.assertEqual(self.client.get_end_effector_laser(), (True, False))


if __name__ == "__main__":
    unittest.main()

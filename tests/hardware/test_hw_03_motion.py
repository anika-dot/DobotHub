"""
Hardware-tests for DobotHub.
Step 3: motion. The arm moves.

WARNING: The arm moves! Keep the workspace clear.
The points to be reached are defined in tests/hardware/base.py (SAFE_POINT, SAFE_POINT_2)
and must be adapted to your own setup.

Run:  pytest --dobot tests/hardware/test_hw_03_motion.py
Without motion:  pytest --dobot -m "not motion"

"""

import time
import unittest

import pytest

from DobotHub.types import MODE_PTP
from tests.hardware.base import ANGLE_TOLERANCE, SAFE_POINT, SAFE_POINT_2, HardwareTestCase

pytestmark = pytest.mark.motion


class MotionTestCase(HardwareTestCase):
    """Base class: clears alarms once and starts every test at SAFE_POINT."""

    @classmethod
    def setUpClass(cls):
        """Connects and clears alarms that would block motion."""
        super().setUpClass()
        cls.bot.clear_alarms()

    def setUp(self):
        """Moves to the safe start position."""
        self.go_safe()

    def position(self):
        """Returns the current Cartesian position (x, y, z, r)."""
        return self.bot.get_pose_named().position


class TestHome(MotionTestCase):
    """Homing."""

    def test_home_reaches_homing_position(self):
        """home() moves to the position stored in the homing parameters."""
        self.bot.home()
        expected = self.client.get_homing_paramaters()
        self.assertPositionAlmostEqual(self.position(), expected)


class TestMoveTo(MotionTestCase):
    """Absolute point-to-point motion."""

    def test_move_to_movj_xyz(self):
        """MOVJ_XYZ reaches the target point."""
        self.bot.move_to(*SAFE_POINT_2, mode=MODE_PTP.MOVJ_XYZ)
        self.assertPositionAlmostEqual(self.position(), SAFE_POINT_2)

    def test_move_to_movl_xyz(self):
        """MOVL_XYZ (linear) reaches the target point."""
        self.bot.move_to(*SAFE_POINT_2, mode=MODE_PTP.MOVL_XYZ)
        self.assertPositionAlmostEqual(self.position(), SAFE_POINT_2)

    def test_move_to_jump_xyz(self):
        """JUMP_XYZ reaches the target point."""
        self.bot.move_to(*SAFE_POINT_2, mode=MODE_PTP.JUMP_XYZ)
        self.assertPositionAlmostEqual(self.position(), SAFE_POINT_2)

    def test_move_to_without_wait_then_wait(self):
        """move_to(wait=False) followed by wait() reaches the target point."""
        self.bot.move_to(*SAFE_POINT_2, mode=MODE_PTP.MOVJ_XYZ, wait=False)
        self.bot.wait()
        self.assertPositionAlmostEqual(self.position(), SAFE_POINT_2)


class TestRelativeMotion(MotionTestCase):
    """Relative point-to-point motion."""

    def test_move_to_relative(self):
        """move_to_relative() moves by the given Cartesian offset."""
        start = self.position()
        self.bot.move_to_relative(0, 0, 10, 0)
        end = self.position()
        self.assertPositionAlmostEqual(end, (start.x, start.y, start.z + 10, start.r))

    def test_slide_to_relative_moves_joint(self):
        """slide_to_relative() moves joint 1 by the given angle."""
        # MOVJ_INC: values are joint increments (degrees), not mm
        start = self.bot.get_pose_named().joints
        self.bot.slide_to_relative(5, 0, 0, 0)
        end = self.bot.get_pose_named().joints
        self.assertAlmostEqual(end.j1, start.j1 + 5, delta=ANGLE_TOLERANCE)


class TestPath(MotionTestCase):
    """Continuous path following."""

    def test_follow_path(self):
        """follow_path() ends at the last point of an absolute path."""
        x, y, z, _ = SAFE_POINT
        path = [(x + 20, y, z), (x + 20, y + 20, z), (x, y + 20, z), (x, y, z)]
        self.bot.follow_path(path)
        self.assertPositionAlmostEqual(self.position()[:3], path[-1])

    def test_follow_path_relative(self):
        """follow_path_relative() ends at the sum of all offsets."""
        start = self.position()
        self.bot.follow_path_relative([(10, 0, 0), (0, 10, 0)])
        end = self.position()
        self.assertPositionAlmostEqual(end[:3], (start.x + 10, start.y + 10, start.z))


class TestJog(MotionTestCase):
    """Jog motion."""

    def wait_until_still(self, timeout=3.0, interval=0.1, tolerance=0.05):
        """Polls z until it stops changing (arm finished decelerating); fails on timeout."""
        last = self.position().z
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            time.sleep(interval)
            current = self.position().z
            if abs(current - last) < tolerance:
                return current
            last = current
        self.fail(f"Arm still moving {timeout} s after jog stop")

    def test_jog_z_up_and_stop(self):
        """Jogging z upwards raises the arm, direction 0 stops it."""
        start = self.position()
        self.bot.jog("z", 1)
        time.sleep(0.5)
        self.bot.jog("z", 0)
        after_stop = self.wait_until_still()  # arm decelerates, does not stop instantly
        self.assertGreater(after_stop, start.z + 1)

        time.sleep(0.5)                      # after stop, nothing should move anymore
        self.assertAlmostEqual(self.position().z, after_stop, delta=0.5)


if __name__ == "__main__":
    unittest.main()

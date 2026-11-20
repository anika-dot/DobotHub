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
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bot.clear_alarms()

    def setUp(self):
        self.go_safe()

    def position(self):
        return self.bot.get_pose_named().position


class TestHome(MotionTestCase):
    def test_home_reaches_homing_position(self):
        self.bot.home()
        expected = self.client.get_homing_paramaters()
        self.assertPositionAlmostEqual(self.position(), expected)


class TestMoveTo(MotionTestCase):
    def test_move_to_movj_xyz(self):
        self.bot.move_to(*SAFE_POINT_2, mode=MODE_PTP.MOVJ_XYZ)
        self.assertPositionAlmostEqual(self.position(), SAFE_POINT_2)

    def test_move_to_movl_xyz(self):
        self.bot.move_to(*SAFE_POINT_2, mode=MODE_PTP.MOVL_XYZ)
        self.assertPositionAlmostEqual(self.position(), SAFE_POINT_2)

    def test_move_to_jump_xyz(self):
        self.bot.move_to(*SAFE_POINT_2, mode=MODE_PTP.JUMP_XYZ)
        self.assertPositionAlmostEqual(self.position(), SAFE_POINT_2)

    def test_move_to_without_wait_then_wait(self):
        self.bot.move_to(*SAFE_POINT_2, mode=MODE_PTP.MOVJ_XYZ, wait=False)
        self.bot.wait()
        self.assertPositionAlmostEqual(self.position(), SAFE_POINT_2)


class TestRelativeMotion(MotionTestCase):
    def test_move_to_relative(self):
        start = self.position()
        self.bot.move_to_relative(0, 0, 10, 0)
        end = self.position()
        self.assertPositionAlmostEqual(end, (start.x, start.y, start.z + 10, start.r))

    def test_slide_to_relative_moves_joint(self):
        # MOVJ_INC: values are joint increments (degrees), not mm
        start = self.bot.get_pose_named().joints
        self.bot.slide_to_relative(5, 0, 0, 0)
        end = self.bot.get_pose_named().joints
        self.assertAlmostEqual(end.j1, start.j1 + 5, delta=ANGLE_TOLERANCE)


class TestPath(MotionTestCase):
    def test_follow_path(self):
        x, y, z, _ = SAFE_POINT
        path = [(x + 20, y, z), (x + 20, y + 20, z), (x, y + 20, z), (x, y, z)]
        self.bot.follow_path(path)
        self.assertPositionAlmostEqual(self.position()[:3], path[-1])

    def test_follow_path_relative(self):
        start = self.position()
        self.bot.follow_path_relative([(10, 0, 0), (0, 10, 0)])
        end = self.position()
        self.assertPositionAlmostEqual(end[:3], (start.x + 10, start.y + 10, start.z))


class TestJog(MotionTestCase):
    def test_jog_z_up_and_stop(self):
        start = self.position()
        self.bot.jog("z", 1)
        time.sleep(0.5)
        self.bot.jog("z", 0)
        time.sleep(0.3)
        after_stop = self.position()
        self.assertGreater(after_stop.z, start.z + 1)

        time.sleep(0.5)                      # after stop, nothing should move anymore
        self.assertAlmostEqual(self.position().z, after_stop.z, delta=0.5)


if __name__ == "__main__":
    unittest.main()

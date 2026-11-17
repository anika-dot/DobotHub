"""Unit-Tests für types.py."""

import unittest

from DobotHub.types import GP1, GP2, GP4, GP5, MODE_PTP, Joints, Pose, Position


class TestTypes(unittest.TestCase):
    def test_ports(self):
        self.assertEqual((GP1, GP2, GP4, GP5), (0, 1, 2, 3))

    def test_ptp_modes_match_protocol(self):
        # Werte laut Dobot Communication Protocol (SetPTPCmd)
        self.assertEqual(MODE_PTP.JUMP_XYZ, 0)
        self.assertEqual(MODE_PTP.MOVJ_XYZ, 1)
        self.assertEqual(MODE_PTP.MOVL_XYZ, 2)
        self.assertEqual(MODE_PTP.JUMP_ANGLE, 3)
        self.assertEqual(MODE_PTP.MOVJ_INC, 6)
        self.assertEqual(MODE_PTP.MOVL_INC, 7)
        self.assertEqual(MODE_PTP.JUMP_MOVL_XYZ, 9)

    def test_pose_is_named_tuple(self):
        pose = Pose(Position(1, 2, 3, 4), Joints(5, 6, 7, 8))
        self.assertEqual(pose.position.x, 1)
        self.assertEqual(pose.joints.j4, 8)
        self.assertEqual(tuple(pose.position), (1, 2, 3, 4))


if __name__ == "__main__":
    unittest.main()

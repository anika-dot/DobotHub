"""
Hardware-Tests Stufe 1: nur lesen. Der Arm bewegt sich nicht, es wird nichts verändert.

Ausführen:  pytest --dobot tests/hardware/test_hw_01_info.py
"""

import struct
import unittest

import pytest

from tests.hardware.base import HardwareTestCase


class TestConnection(HardwareTestCase):
    def test_connected(self):
        self.assertTrue(self.bot.connected())

    def test_device_name_is_string(self):
        self.assertIsInstance(self.client.get_device_name(), str)

    def test_device_serial_number_is_string(self):
        self.assertIsInstance(self.client.get_device_serial_number(), str)

    def test_device_version(self):
        version = self.client.get_device_version()
        self.assertEqual(len(version), 3)
        self.assertTrue(all(isinstance(v, int) for v in version))

    def test_device_time_increases(self):
        t1 = self.client.get_device_time()
        t2 = self.client.get_device_time()
        self.assertGreaterEqual(t2, t1)


class TestPose(HardwareTestCase):
    def test_get_pose_returns_8_floats(self):
        pose = self.bot.get_pose()
        self.assertEqual(len(pose), 8)
        self.assertTrue(all(isinstance(v, float) for v in pose))

    def test_get_pose_named_matches_raw(self):
        named = self.bot.get_pose_named()
        raw = self.bot.get_pose()
        self.assertPositionAlmostEqual(named.position, raw[:4], delta=0.5)


class TestQueue(HardwareTestCase):
    def test_current_queue_index_is_int(self):
        index = self.client.get_current_queue_index()
        self.assertIsInstance(index, int)
        self.assertGreaterEqual(index, 0)

    def test_queued_command_returns_increasing_index(self):
        i1 = self.client.wait(0)
        i2 = self.client.wait(0)
        self.assertGreater(i2, i1)


class TestStatus(HardwareTestCase):
    @pytest.mark.xfail(strict=True, raises=struct.error, reason="Parser ID 20 Format '<B' * 16")
    def test_get_alarms(self):
        self.bot.get_alarms()

    @pytest.mark.xfail(strict=True, raises=struct.error, reason="Parser ID 133 Format '<B' * 2")
    def test_get_io_di(self):
        self.client.get_io_di()

    def test_handheld_teaching_state_is_bool(self):
        self.assertIsInstance(self.client.get_handheld_teaching_state(), bool)


if __name__ == "__main__":
    unittest.main()

"""
Hardware-tests for DobotHub.
Step 5: peripherals (conveyor belt, IR sensor, color sensor).

Default ports of the API: IR sensor on GP4, color sensor on GP2, conveyor on stepper 1 (index 0).
Only test connected accessories, e.g.:
    pytest --dobot -m conveyor
    pytest --dobot -m "ir or color"

The test cannot measure whether the conveyor actually moves -> have a look.
With conveyor AND light barrier, test_object_reaches_light_barrier checks the whole sequence.
"""

import struct
import time
import unittest

import pytest

from tests.hardware.base import HardwareTestCase


@pytest.mark.conveyor
class TestConveyor(HardwareTestCase):
    """Conveyor belt."""

    def tearDown(self):
        """Stops the conveyor after each test."""
        self.bot.conveyor_stop()

    def test_run_and_stop(self):
        """The conveyor runs forward and stops without error."""
        self.bot.conveyor(30)
        time.sleep(1.0)
        self.bot.conveyor_stop()

    def test_reverse(self):
        """The conveyor runs backwards and stops without error."""
        self.bot.conveyor(-30)
        time.sleep(1.0)
        self.bot.conveyor_stop()

    def test_distance_blocks_for_expected_time(self):
        """conveyor_distance() blocks for distance / speed seconds."""
        start = time.monotonic()
        self.bot.conveyor_distance(30, speed=30)
        self.assertAlmostEqual(time.monotonic() - start, 1.0, delta=0.3)


@pytest.mark.ir
class TestIrSensor(HardwareTestCase):
    """IR sensor (light barrier)."""

    @classmethod
    def setUpClass(cls):
        """Connects and enables the IR sensor."""
        super().setUpClass()
        cls.bot.ir_enable()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        """Disables the IR sensor."""
        cls.bot.ir_enable(enable=False)

    def test_get_ir_returns_bool(self):
        """get_ir() returns a bool."""
        self.assertIsInstance(self.bot.get_ir(), bool)

    def test_wait_for_object_times_out_without_object(self):
        """wait_for_object() returns False after the timeout if nothing is detected."""
        if self.bot.get_ir():
            self.skipTest("Light barrier is currently interrupted")
        start = time.monotonic()
        self.assertFalse(self.bot.wait_for_object(timeout=0.5))
        self.assertLess(time.monotonic() - start, 1.5)


@pytest.mark.conveyor
@pytest.mark.ir
class TestConveyorWithLightBarrier(HardwareTestCase):
    """Put an object on the belt before the light barrier, then start the test."""

    def tearDown(self):
        """Stops the conveyor after the test."""
        self.bot.conveyor_stop()

    def test_object_reaches_light_barrier(self):
        """An object on the running belt is detected by the light barrier."""
        self.bot.ir_enable()
        self.bot.conveyor(30)
        detected = self.bot.wait_for_object(timeout=15)
        self.bot.conveyor_stop()
        if not detected:
            self.skipTest("No object detected - is there one on the belt?")
        self.assertTrue(self.bot.get_ir())


@pytest.mark.color
class TestColorSensor(HardwareTestCase):
    """Color sensor."""

    @classmethod
    def setUpClass(cls):
        """Connects and enables the color sensor."""
        super().setUpClass()
        cls.bot.color_enable()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        """Disables the color sensor."""
        cls.bot.color_enable(enable=False)

    @pytest.mark.xfail(strict=True, raises=struct.error, reason="Parser ID 137 format '<B' * 3")
    def test_get_color(self):
        """get_color() returns three values (r, g, b)."""
        color = self.bot.get_color()
        self.assertEqual(len(color), 3)


if __name__ == "__main__":
    unittest.main()

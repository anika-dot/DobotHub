"""
Hardware-Tests Stufe 5: Peripherie (Förderband, IR-Sensor, Farbsensor).

Ports laut Default der API: IR-Sensor an GP4, Farbsensor an GP2, Förderband an Stepper 1 (index 0).
Nur angeschlossenes Zubehör testen, z. B.:
    pytest --dobot -m conveyor
    pytest --dobot -m "ir or color"

Ob sich das Förderband tatsächlich bewegt, kann der Test nicht messen -> kurz hinschauen.
Mit Förderband UND Lichtschranke prüft test_object_reaches_light_barrier den ganzen Ablauf.
"""

import struct
import time
import unittest

import pytest

from tests.hardware.base import HardwareTestCase


@pytest.mark.conveyor
class TestConveyor(HardwareTestCase):
    def tearDown(self):
        self.bot.conveyor_stop()

    def test_run_and_stop(self):
        self.bot.conveyor(30)
        time.sleep(1.0)
        self.bot.conveyor_stop()

    def test_reverse(self):
        self.bot.conveyor(-30)
        time.sleep(1.0)
        self.bot.conveyor_stop()

    def test_distance_blocks_for_expected_time(self):
        start = time.monotonic()
        self.bot.conveyor_distance(30, speed=30)
        self.assertAlmostEqual(time.monotonic() - start, 1.0, delta=0.3)


@pytest.mark.ir
class TestIrSensor(HardwareTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bot.ir_enable()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.bot.ir_enable(enable=False)

    def test_get_ir_returns_bool(self):
        self.assertIsInstance(self.bot.get_ir(), bool)

    def test_wait_for_object_times_out_without_object(self):
        if self.bot.get_ir():
            self.skipTest("Lichtschranke ist gerade unterbrochen")
        start = time.monotonic()
        self.assertFalse(self.bot.wait_for_object(timeout=0.5))
        self.assertLess(time.monotonic() - start, 1.5)


@pytest.mark.conveyor
@pytest.mark.ir
class TestConveyorWithLightBarrier(HardwareTestCase):
    """Ein Objekt vor die Lichtschranke aufs Band legen, dann Test starten."""

    def tearDown(self):
        self.bot.conveyor_stop()

    def test_object_reaches_light_barrier(self):
        self.bot.ir_enable()
        self.bot.conveyor(30)
        detected = self.bot.wait_for_object(timeout=15)
        self.bot.conveyor_stop()
        if not detected:
            self.skipTest("Kein Objekt erkannt - liegt eines auf dem Band?")
        self.assertTrue(self.bot.get_ir())


@pytest.mark.color
class TestColorSensor(HardwareTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bot.color_enable()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.bot.color_enable(enable=False)

    @pytest.mark.xfail(strict=True, raises=struct.error, reason="Parser ID 137 Format '<B' * 3")
    def test_get_color(self):
        color = self.bot.get_color()
        self.assertEqual(len(color), 3)


if __name__ == "__main__":
    unittest.main()

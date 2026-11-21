"""
Unit-Tests for client.py with a simulated serial interface (FakeSerial).

Each method is tested for:
- which packet is sent (ID, rw-bit, queued-bit, parameter bytes)
- how the Dobot's response is translated into a return value
"""

import struct
import unittest
from unittest.mock import patch

import pytest

from DobotHub.client import Client
from DobotHub.exceptions import DobotError
from DobotHub.types import GP4
from tests.helpers import Frame, FakeSerial, floats, frame, uint64


def B(*values):
    """
    Converts a list of integers (0-255) into a list of bytes (as sent
    by the Dobot). Used for boolean flags and small integers.
    """
    return list(values)

# --- Method, Argument, Expected Packet (Frame)
REQUEST_CASES = [
    # device information
    ("get_device_serial_number", (), Frame(0, False, False, [])),
    ("get_device_name", (), Frame(1, False, False, [])),
    ("set_device_name", ("Dobot",), Frame(1, True, False, list(b"Dobot\x00"))),
    ("get_device_version", (), Frame(2, False, False, [])),
    ("get_device_time", (), Frame(4, False, False, [])),
    ("get_device_id", (), Frame(5, False, False, [])),
    # pose
    ("get_pose", (), Frame(10, False, False, [])),
    ("reset_pose", (1, 10.0, 20.0), Frame(11, True, False, list(struct.pack("<Bff", 1, 10, 20)))),
    # alarm
    ("get_alarms_state", (), Frame(20, False, False, [])),
    ("clear_alarms_state", (), Frame(21, True, False, [])),
    # homing
    ("get_homing_paramaters", (), Frame(30, False, False, [])),
    ("set_homing_parameters", (200, 0, 50, 0), Frame(30, True, True, floats(200, 0, 50, 0))),
    ("set_homing_command", (0,), Frame(31, True, True, floats(0))),
    ("home", (), Frame(31, True, True, floats(0))),
    # end effector parameters
    ("get_end_effector_gripper", (), Frame(63, False, False, [])),
    ("set_end_effector_gripper", (True, True), Frame(63, True, True, B(1, 1))),
    ("set_end_effector_gripper", (True, False), Frame(63, True, True, B(1, 0))),
    ("set_end_effector_suction_cup", (True, True), Frame(62, True, True, B(1, 1))),
    ("set_end_effector_laser", (True, False), Frame(61, True, True, B(1, 0))),
    # jog
    ("set_jog_common_params", (50, 50), Frame(72, True, True, floats(50, 50))),
    ("set_jog_command", (0, 1), Frame(73, True, True, B(0, 1))),
    ("set_jog_joint_params", ([1, 2, 3, 4], [5, 6, 7, 8]), Frame(70, True, True, floats(1, 2, 3, 4, 5, 6, 7, 8))),
    # PTP
    ("set_point_to_point_joint_params", ([100] * 4, [100] * 4), Frame(80, True, True, floats(*[100] * 8))),
    ("set_point_to_point_coordinate_params", (100, 100, 100, 100), Frame(81, True, True, floats(100, 100, 100, 100))),
    ("set_point_to_point_jump_params", (10, 10), Frame(82, True, True, floats(10, 10))),
    ("set_point_to_point_common_params", (50, 60), Frame(83, True, True, floats(50, 60))),
    ("set_point_to_point_command", (1, 200, 0, 50, 0),
     Frame(84, True, True, list(struct.pack("<Bffff", 1, 200, 0, 50, 0)))),
    ("set_point_to_point_command", (1, 200, 0, 50, 0, False),
     Frame(84, True, False, list(struct.pack("<Bffff", 1, 200, 0, 50, 0)))),
    ("set_point_to_point_jump2_params", (5, 5, 5), Frame(87, True, True, floats(5, 5, 5))),
    # CP
    ("set_continous_trajectory_params", (50, 50, 50), Frame(90, True, True, list(struct.pack("<fffB", 50, 50, 50, 0)))),
    ("set_continous_trajectory_real_time_params", (50, 50, 10),
     Frame(90, True, True, list(struct.pack("<fffB", 50, 50, 10, 1)))),
    ("set_continous_trajectory_command", (1, 200, 0, 50, 50),
     Frame(91, True, True, list(struct.pack("<Bffff", 1, 200, 0, 50, 50)))),
    # ARC
    ("set_arc_command", ([1, 2, 3, 4], [5, 6, 7, 8]), Frame(101, True, True, floats(1, 2, 3, 4, 5, 6, 7, 8))),
    # Wait / Trigger
    ("wait", (500,), Frame(110, True, True, list(struct.pack("<L", 500)))),
    ("set_trigger_command", (1, 0, 2, 1000), Frame(120, True, True, list(struct.pack("<BBBH", 1, 0, 2, 1000)))),
    # IO / Peripherie
    ("set_io_do", (2, 1), Frame(131, True, True, B(2, 1))),
    ("set_extended_motor_velocity", (0, True, 1000), Frame(135, True, True, list(struct.pack("<BBf", 0, 1, 1000)))),
    ("set_color_sensor", (0, 1, 1, 1), Frame(137, True, True, B(1, 1, 1))),
    ("set_ir_switch", (0, 1, GP4, 1), Frame(138, True, True, B(1, GP4, 1))),
    ("get_ir_switch", (GP4,), Frame(138, False, False, B(GP4))),
    # queue control
    ("start_queue", (), Frame(240, True, False, [])),
    ("stop_queue", (), Frame(241, True, False, [])),
    ("stop_queue", (True,), Frame(242, True, False, [])),
    ("stop_queue_download", (), Frame(244, True, False, [])),
    ("clear_queue", (), Frame(245, True, False, [])),
    ("get_current_queue_index", (), Frame(246, True, False, [])),
]


class ClientTestCase(unittest.TestCase):
    """
    Base class for Client tests. Sets up a FakeSerial and a Client instance.
    """

    def setUp(self):
        self.fake = FakeSerial()
        patcher = patch("DobotHub.client.serial.Serial", return_value=self.fake)
        self.serial_cls = patcher.start()
        self.addCleanup(patcher.stop)
        self.client = Client("COM_TEST")


class TestConnection(ClientTestCase):
    """
    Tests for the connection functionality of the Client.
    """
    def test_opens_port_with_dobot_settings(self):
        """
        Checks that the Client opens the serial port with the correct settings for the Dobot.
        """
        kwargs = self.serial_cls.call_args.kwargs
        self.assertEqual(kwargs["port"], "COM_TEST")
        self.assertEqual(kwargs["baudrate"], 115200)

    def test_connected_and_close(self):
        """
        Tests that the Client reports being connected and can be closed.
        """
        self.assertTrue(self.client.connected())
        self.client.close()
        self.assertFalse(self.client.connected())

    def test_close_twice_is_safe(self):
        """
        Tests that calling close() on the Client twice does not raise an exception.
        """
        self.client.close()
        self.client.close()


class TestRequests(ClientTestCase):
    """
    Tests that Client methods send the expected frames to the Dobot.
    """
    def test_methods_send_expected_frames(self):
        """
        For each method in REQUEST_CASES, calls the method with the given arguments
        and checks that the last request sent matches the expected Frame.
        """
        for name, args, expected in REQUEST_CASES:
            with self.subTest(method=name, args=args):
                # for each case, create a fresh Client to avoid interference from previous calls
                # a parsing error in the (empty) Fake response should not affect other cases
                self.setUp()
                try:
                    getattr(self.client, name)(*args)
                except (struct.error, IndexError):
                    pass   # Here, only the sent request is checked, not the response.
                self.assertEqual(len(self.fake.requests), 1, "exactly one packet expected")
                self.assertEqual(self.fake.last, expected)

    def test_raw_frame_of_get_pose(self):
        """
        Tests that get_pose() sends the correct raw frame to the Dobot.
        """
        self.fake.responses[10] = floats(*[0] * 8)
        self.client.get_pose()
        self.assertEqual(self.fake.written, bytes([0xAA, 0xAA, 0x02, 0x0A, 0x00, 0xF6]))

    def test_send_holds_lock_only_during_call(self):
        """
        Tests that the Client's lock is held only during the send() call and is released afterwards.
        """
        self.fake.responses[246] = uint64(1)
        self.client.get_current_queue_index()
        self.assertFalse(self.client.lock.locked())


class TestResponses(ClientTestCase):
    """
    Tests that Client methods correctly interpret the responses from the Dobot.
    """
    def test_get_device_name(self):
        """
        Tests that get_device_name() returns the correct device name.
        """
        self.fake.responses[1] = list(b"Dobot")
        self.assertEqual(self.client.get_device_name(), "Dobot")

    def test_get_pose(self):
        """
        Tests that get_pose() returns the correct pose.
        """
        pose = (200.0, 0.0, 50.0, 0.0, 0.0, 45.0, 45.0, 0.0)
        self.fake.responses[10] = floats(*pose)
        self.assertEqual(self.client.get_pose(), pose)

    def test_get_device_version(self):
        """
        Tests that get_device_version() returns the correct device version.
        """
        self.fake.responses[2] = [3, 7, 0]
        self.assertEqual(self.client.get_device_version(), [3, 7, 0])

    def test_queued_command_returns_queue_index(self):
        """
        Tests that queued commands return the correct queue index.
        """
        self.fake.queue_index = 17
        self.assertEqual(self.client.set_point_to_point_command(1, 200, 0, 50, 0), 17)
        self.assertEqual(self.client.wait(0), 18)

    def test_get_current_queue_index(self):
        """
        Tests that get_current_queue_index() returns the correct queue index.
        """
        self.fake.responses[246] = uint64(99)
        self.assertEqual(self.client.get_current_queue_index(), 99)

    def test_get_ir_state(self):
        """
        Tests that get_ir_state() returns the correct state of the IR sensor.
        """
        self.fake.responses[138] = [1]
        self.assertTrue(self.client.get_ir_state(GP4))
        self.fake.responses[138] = [0]
        self.assertFalse(self.client.get_ir_state(GP4))

    def test_get_homing_parameters(self):
        """
        Tests that get_homing_parameters() returns the correct homing parameters.
        """
        self.fake.responses[30] = floats(200, 0, 50, 0)
        self.assertEqual(self.client.get_homing_paramaters(), (200, 0, 50, 0))


class TestConveyorConversion(ClientTestCase):
    """
    Tests the conversion from mm/s to pulses for the conveyor speed.
    """
    def test_mm_per_second_to_pulses(self):
        """
        Tests that set_conveyor_speed() correctly converts mm/s to pulses and calls set_extended_motor
        """
        with patch.object(self.client, "set_extended_motor_velocity") as motor:
            self.client.set_conveyor_speed(50)
        pulses = 50 * (360.0 / 1.8 * 10.0 * 16.0) / (3.1415926535898 * 36.0)
        motor.assert_called_once()
        index, enable, value, queue = motor.call_args.args
        self.assertEqual((index, enable, queue), (0, True, True))
        self.assertAlmostEqual(value, pulses, places=6)

    def test_negative_speed_reverses(self):
        """
        Tests that set_conveyor_speed() correctly handles negative speeds by reversing the direction.
        """
        with patch.object(self.client, "set_extended_motor_velocity") as motor:
            self.client.set_conveyor_speed(-50, index=1)
        self.assertLess(motor.call_args.args[2], 0)
        self.assertEqual(motor.call_args.args[0], 1)

    def test_zero_speed_stops(self):
        """
        Tests that set_conveyor_speed() correctly handles zero speed by stopping the motor.
        """
        with patch.object(self.client, "set_extended_motor_velocity") as motor:
            self.client.set_conveyor_speed(0)
        self.assertEqual(motor.call_args.args[2], 0)


class TestWaitUntilDone(ClientTestCase):
    """
    Tests the wait_until_done() method of the Client.
    """
    @patch("DobotHub.client.sleep")
    def test_waits_until_target_index_reached(self, sleep):
        """
        Tests that wait_until_done() waits until the target queue index is reached.
        """
        with patch.object(self.client, "get_current_queue_index", side_effect=[3, 4, 5]) as idx:
            self.client.wait_until_done(5)
        self.assertEqual(idx.call_count, 3)


class TestKnownBugs(ClientTestCase):
    """
    Tests for known bugs in the Client implementation.
    """
    @pytest.mark.xfail(strict=True, reason="send() does not release the lock when an exception occurs "
                                           "-> Any subsequent call will be blocked indefinitely (use `with self.lock:`)")
    def test_lock_released_on_error(self):
        """The lock is released even if parsing the response fails."""
        self.fake.responses[10] = floats(1, 2, 3)   # Pose too short -> struct.error during parsing in send()
        with self.assertRaises(struct.error):
            self.client.get_pose()
        self.assertFalse(self.client.lock.locked())

    @pytest.mark.xfail(strict=True, reason="Message.read returns None -> send() raises AttributeError instead of DobotError")
    def test_invalid_response_raises_dobot_error(self):
        """A response with a wrong header raises a DobotError."""
        self.fake.auto_respond = False
        self.fake.queue(b"\x00\x00\x00")
        with self.assertRaises(DobotError):
            self.client.get_pose()

    @pytest.mark.xfail(strict=True, reason="Message.read returns None on timeout -> AttributeError instead of DobotError")
    def test_timeout_raises_dobot_error(self):
        """A missing response (timeout) raises a DobotError."""
        self.fake.auto_respond = False
        with self.assertRaises(DobotError):
            self.client.get_pose()

    @pytest.mark.xfail(strict=True, raises=struct.error, reason="Parser ID 60 packs 4 floats, method passes 3")
    def test_set_end_effector_params(self):
        """set_end_effector_params() sends the three offsets as floats."""
        self.client.set_end_effector_params(1.0, 2.0, 3.0)
        self.assertEqual(self.fake.last, Frame(60, True, False, floats(1, 2, 3)))

    @pytest.mark.xfail(strict=True, raises=struct.error,
                       reason="Parser ID 89 expects 6 values (Bfffff), method passes 3")
    def test_set_point_to_point_sliding_rail_po_command(self):
        """set_point_to_point_sliding_rail_po_command() can be sent."""
        self.client.set_point_to_point_sliding_rail_po_command(50, 1, 1)

    @pytest.mark.xfail(strict=True, raises=struct.error, reason="Parser ID 137 format '<B' * 3")
    def test_get_color_sensor(self):
        """get_color_sensor() returns (r, g, b)."""
        self.fake.responses[137] = [10, 20, 30]
        self.assertEqual(self.client.get_color_sensor(0), (10, 20, 30))

    @pytest.mark.xfail(strict=True, raises=struct.error, reason="Parser ID 20 format '<B' * 16")
    def test_get_alarms_state(self):
        """get_alarms_state() can parse the 16-byte alarm response."""
        self.fake.responses[20] = [0] * 16
        self.client.get_alarms_state()

    @pytest.mark.xfail(strict=True, raises=IndexError,
                       reason="Response to a non-queued setter (rw=1, queued=0) is read with the getter parser; "
                              "the response has no params -> x[0] fails")
    def test_non_queued_setter_with_empty_response(self):
        """A non-queued setter with an empty response does not fail."""
        self.client.set_handheld_teaching_mode(1)


if __name__ == "__main__":
    unittest.main()

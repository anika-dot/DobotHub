"""
Unit tests for dobot.py (high-level API).

The Client is fully replaced by a MagicMock. The tests check whether the API calls the right
Client methods with the right arguments. `sleep` is patched so the tests do not wait.
"""

import unittest
from types import SimpleNamespace
from unittest.mock import call, patch

from DobotHub.dobot import Dobot, find_port
from DobotHub.exceptions import DobotConnectionError, DobotError
from DobotHub.types import GP2, GP4, MODE_PTP, Joints, Pose, Position


class DobotTestCase(unittest.TestCase):
    """Base class: Dobot with a mocked Client and patched sleep."""

    def setUp(self):
        """Creates a Dobot with a mocked Client and resets the calls made by __init__."""
        client_patcher = patch("DobotHub.dobot.Client")
        self.client_cls = client_patcher.start()
        self.addCleanup(client_patcher.stop)

        sleep_patcher = patch("DobotHub.dobot.sleep")
        self.sleep = sleep_patcher.start()
        self.addCleanup(sleep_patcher.stop)

        self.bot = Dobot("COM_TEST")
        self.client = self.bot.client
        self.client.reset_mock()          # do not count calls from __init__


class WaitPatchedTestCase(DobotTestCase):
    """Base class that additionally replaces Dobot.wait() with a mock."""

    def setUp(self):
        """Patches Dobot.wait() so it can be checked whether it was called."""
        super().setUp()
        wait_patcher = patch.object(Dobot, "wait")
        self.wait = wait_patcher.start()
        self.addCleanup(wait_patcher.stop)


class TestInit(unittest.TestCase):
    """Dobot constructor."""

    @patch("DobotHub.dobot.Client")
    def test_opens_client_on_port(self, client_cls):
        """The Client is created with the given port."""
        Dobot("COM7")
        client_cls.assert_called_once_with("COM7")

    @patch("DobotHub.dobot.Client")
    def test_resets_and_starts_queue_first(self, client_cls):
        """The queue is stopped, cleared and started before anything else."""
        Dobot("COM7")
        calls = client_cls.return_value.method_calls
        self.assertEqual(calls[:3], [call.stop_queue(True), call.clear_queue(), call.start_queue()])

    @patch("DobotHub.dobot.Client")
    def test_sets_default_motion_params(self, client_cls):
        """Default PTP and CP motion parameters are set."""
        Dobot("COM7")
        c = client_cls.return_value
        c.set_point_to_point_common_params.assert_called_once_with(100, 100)
        c.set_point_to_point_jump_params.assert_called_once_with(10, 10)
        c.set_continous_trajectory_params.assert_called_once_with(50, 50, 50)


class TestFindPort(unittest.TestCase):
    """Automatic port detection."""

    @patch("DobotHub.dobot.list_ports.comports")
    def test_finds_dobot_by_vid(self, comports):
        """The port with USB VID 4292 is returned."""
        comports.return_value = [
            SimpleNamespace(vid=1234, device="COM1"),
            SimpleNamespace(vid=4292, device="COM5"),
        ]
        self.assertEqual(find_port(), "COM5")

    @patch("DobotHub.dobot.list_ports.comports")
    def test_second_vid(self, comports):
        """The port with USB VID 6790 is returned."""
        comports.return_value = [SimpleNamespace(vid=6790, device="COM9")]
        self.assertEqual(find_port(), "COM9")

    @patch("DobotHub.dobot.list_ports.comports", return_value=[SimpleNamespace(vid=None, device="COM1")])
    def test_raises_if_no_dobot(self, _):
        """DobotConnectionError is raised if no Dobot is found."""
        with self.assertRaises(DobotConnectionError):
            find_port()

    def test_connection_error_is_dobot_error(self):
        """DobotConnectionError is a subclass of DobotError."""
        self.assertTrue(issubclass(DobotConnectionError, DobotError))


class TestPose(DobotTestCase):
    """Pose and connection status."""

    def test_get_pose_passes_through(self):
        """get_pose() returns the raw Client value."""
        self.client.get_pose.return_value = (1, 2, 3, 4, 5, 6, 7, 8)
        self.assertEqual(self.bot.get_pose(), (1, 2, 3, 4, 5, 6, 7, 8))

    def test_get_pose_named(self):
        """get_pose_named() maps the values to Position and Joints."""
        self.client.get_pose.return_value = (200, 0, 50, 10, 1, 45, 30, 9)
        pose = self.bot.get_pose_named()
        self.assertEqual(pose, Pose(Position(200, 0, 50, 10), Joints(1, 45, 30, 9)))
        self.assertEqual(pose.position.z, 50)
        self.assertEqual(pose.joints.j2, 45)

    def test_connected(self):
        """connected() returns the Client state."""
        self.client.connected.return_value = True
        self.assertTrue(self.bot.connected())


class TestWait(DobotTestCase):
    """Waiting for queued commands."""

    def test_waits_until_marker_reached(self):
        """wait() queues a zero wait and polls until its index is reached."""
        self.client.wait.return_value = 11
        self.client.get_current_queue_index.side_effect = [10, 10, 11]
        self.bot.wait()
        self.client.wait.assert_called_once_with(0)
        self.assertEqual(self.client.get_current_queue_index.call_count, 3)
        self.assertEqual(self.sleep.call_count, 2)

    def test_returns_when_queue_already_done(self):
        """wait() returns at once if the Dobot is already at the marker (idle queue)."""
        self.client.wait.return_value = 7
        self.client.get_current_queue_index.return_value = 7
        self.bot.wait()
        self.assertEqual(self.client.get_current_queue_index.call_count, 1)
        self.sleep.assert_not_called()

    def test_waits_for_given_index(self):
        """wait(index) also waits for the marker queued after that index."""
        self.client.wait.return_value = 6
        self.client.get_current_queue_index.side_effect = [3, 4, 5, 6]
        self.bot.wait(5)
        self.assertEqual(self.client.get_current_queue_index.call_count, 4)


class TestMotion(WaitPatchedTestCase):
    """Homing, point-to-point motion, paths and jog."""

    def test_home(self):
        """home() sends the homing command and waits."""
        self.bot.home()
        self.client.set_homing_command.assert_called_once_with(0)
        self.wait.assert_called_once()

    def test_home_without_wait(self):
        """home(wait=False) does not wait."""
        self.bot.home(wait=False)
        self.wait.assert_not_called()

    def test_set_home(self):
        """set_home() sets the homing parameters with r=0 by default."""
        self.bot.set_home(200, 0, 50)
        self.client.set_homing_parameters.assert_called_once_with(200, 0, 50, 0)

    def test_move_to_passes_mode(self):
        """move_to() passes the given PTP mode to the Client."""
        self.bot.move_to(200, 0, 50, 0, mode=MODE_PTP.MOVL_XYZ)
        self.client.set_point_to_point_command.assert_called_once_with(MODE_PTP.MOVL_XYZ, 200, 0, 50, 0)
        self.wait.assert_called_once()

    def test_move_to_without_wait(self):
        """move_to(wait=False) does not wait."""
        self.bot.move_to(200, 0, 50, 0, wait=False)
        self.wait.assert_not_called()

    def test_move_to_relative_uses_cartesian_increment(self):
        """move_to_relative() uses mode MOVL_INC."""
        self.bot.move_to_relative(0, 0, 10, 0)
        self.client.set_point_to_point_command.assert_called_once_with(MODE_PTP.MOVL_INC, 0, 0, 10, 0)

    def test_slide_to_relative(self):
        """slide_to_relative() uses mode MOVJ_INC."""
        self.bot.slide_to_relative(5, 0, 0, 0, wait=False)
        self.client.set_point_to_point_command.assert_called_once_with(MODE_PTP.MOVJ_INC, 5, 0, 0, 0)

    def test_speed(self):
        """speed() sets the PTP common and coordinate parameters."""
        self.bot.speed(30, 40)
        self.client.set_point_to_point_common_params.assert_called_once_with(30, 40)
        self.client.set_point_to_point_coordinate_params.assert_called_once_with(30, 30, 40, 40)

    def test_follow_path(self):
        """follow_path() queues one CP command per point and waits for the last one."""
        self.client.set_continous_trajectory_command.side_effect = [11, 12, 13]
        path = [(200, 0, 50), (210, 0, 50), (210, 10, 50)]
        self.bot.follow_path(path)

        self.client.stop_queue.assert_called_once_with()
        self.assertEqual(self.client.set_continous_trajectory_command.call_args_list,
                         [call(1, x, y, z, 50) for x, y, z in path])
        self.client.start_queue.assert_called_once_with()
        self.wait.assert_called_once_with(13)    # waits for the last point

    def test_follow_path_relative(self):
        """follow_path_relative() uses CP mode 0 (relative)."""
        self.bot.follow_path_relative([(10, 0, 0)], wait=False)
        self.client.set_continous_trajectory_command.assert_called_once_with(0, 10, 0, 0, 50)
        self.wait.assert_not_called()

    def test_jog_mapping(self):
        """jog() maps axis and direction to the correct jog command."""
        cases = {("x", 1): 1, ("x", -1): 2, ("y", 1): 3, ("y", -1): 4,
                 ("z", 1): 5, ("z", -1): 6, ("r", 1): 7, ("r", -1): 8, ("x", 0): 0}
        for (axis, direction), cmd in cases.items():
            with self.subTest(axis=axis, direction=direction):
                self.client.reset_mock()
                self.bot.jog(axis, direction)
                self.client.set_jog_command.assert_called_once_with(0, cmd)

    def test_jog_invalid_axis(self):
        """jog() with an unknown axis raises KeyError."""
        with self.assertRaises(KeyError):
            self.bot.jog("a", 1)


class TestAlarms(DobotTestCase):
    """Alarm handling."""

    def test_get_alarms(self):
        """get_alarms() returns the Client alarm state."""
        self.client.get_alarms_state.return_value = 0
        self.assertEqual(self.bot.get_alarms(), 0)

    def test_clear_alarms(self):
        """clear_alarms() calls clear_alarms_state()."""
        self.bot.clear_alarms()
        self.client.clear_alarms_state.assert_called_once_with()


class TestEffectors(WaitPatchedTestCase):
    """Gripper, suction cup and laser."""

    def test_gripper_open(self):
        """gripper_open() opens, queues a 500 ms pause and waits."""
        self.bot.gripper_open()
        self.client.set_end_effector_gripper.assert_called_once_with(True, False)
        self.client.wait.assert_called_once_with(500)
        self.wait.assert_called_once()

    def test_gripper_close(self):
        """gripper_close() closes and queues the given pause."""
        self.bot.gripper_close(delay=200)
        self.client.set_end_effector_gripper.assert_called_once_with(True, True)
        self.client.wait.assert_called_once_with(200)

    def test_gripper_without_delay_and_wait(self):
        """delay=0 and wait=False queue no pause and do not wait."""
        self.bot.gripper_open(wait=False, delay=0)
        self.client.wait.assert_not_called()
        self.wait.assert_not_called()

    def test_gripper_idle(self):
        """gripper_idle() switches the gripper control off."""
        self.bot.gripper_idle()
        self.client.set_end_effector_gripper.assert_called_once_with(False, False)

    def test_suction_on_off(self):
        """suction_on() and suction_off() switch the suction cup."""
        self.bot.suction_on()
        self.client.set_end_effector_suction_cup.assert_called_with(True, True)
        self.bot.suction_off()
        self.client.set_end_effector_suction_cup.assert_called_with(False, False)

    def test_laser(self):
        """laser() switches the laser on and off."""
        self.bot.laser(True)
        self.client.set_end_effector_laser.assert_called_with(True, True)
        self.bot.laser(False, wait=False)
        self.client.set_end_effector_laser.assert_called_with(True, False)


class TestConveyor(DobotTestCase):
    """Conveyor belt."""

    def test_conveyor(self):
        """conveyor() sets the speed on stepper index 0."""
        self.bot.conveyor(50)
        self.client.set_conveyor_speed.assert_called_once_with(50, 0)

    def test_conveyor_stop(self):
        """conveyor_stop() sets speed 0."""
        self.bot.conveyor_stop(index=1)
        self.client.set_conveyor_speed.assert_called_once_with(0, 1)

    def test_conveyor_distance_forward(self):
        """conveyor_distance() runs for distance / speed seconds and stops."""
        self.bot.conveyor_distance(100, speed=50)
        self.assertEqual(self.client.set_conveyor_speed.call_args_list, [call(50, 0), call(0, 0)])
        self.sleep.assert_called_once_with(2.0)

    def test_conveyor_distance_backward(self):
        """A negative distance runs the belt backwards."""
        self.bot.conveyor_distance(-25, speed=50)
        self.assertEqual(self.client.set_conveyor_speed.call_args_list, [call(-50, 0), call(0, 0)])
        self.sleep.assert_called_once_with(0.5)


class TestSensors(DobotTestCase):
    """IR sensor and color sensor."""

    def test_ir_enable(self):
        """ir_enable() enables the IR sensor on GP4."""
        self.bot.ir_enable()
        self.client.set_ir_switch.assert_called_once_with(0, 1, GP4, 1)

    def test_ir_disable(self):
        """ir_enable(enable=False) disables the IR sensor."""
        self.bot.ir_enable(enable=False)
        self.client.set_ir_switch.assert_called_once_with(0, 0, GP4, 1)

    def test_get_ir(self):
        """get_ir() reads the IR state on GP4."""
        self.client.get_ir_state.return_value = True
        self.assertTrue(self.bot.get_ir())
        self.client.get_ir_state.assert_called_once_with(GP4)

    def test_wait_for_object_detects(self):
        """wait_for_object() returns True as soon as an object is detected."""
        self.client.get_ir_state.side_effect = [False, False, True]
        self.assertTrue(self.bot.wait_for_object())
        self.assertEqual(self.sleep.call_count, 2)

    @patch("DobotHub.dobot.time")
    def test_wait_for_object_timeout(self, time):
        """wait_for_object() returns False after the timeout."""
        time.side_effect = [0.0, 0.5, 1.5]        # start, 1st check, 2nd check (> timeout)
        self.client.get_ir_state.return_value = False
        self.assertFalse(self.bot.wait_for_object(timeout=1.0))

    def test_color_enable(self):
        """color_enable() enables the color sensor on GP2."""
        self.bot.color_enable()
        self.client.set_color_sensor.assert_called_once_with(0, 1, GP2, 1)

    def test_get_color(self):
        """get_color() returns the Client color value."""
        self.client.get_color_sensor.return_value = (1, 0, 0)
        self.assertEqual(self.bot.get_color(), (1, 0, 0))


class TestClose(DobotTestCase):
    """Shutdown."""

    def test_close_stops_everything(self):
        """close() stops conveyor and effectors and closes the connection last."""
        self.bot.close()
        self.client.set_conveyor_speed.assert_called_once_with(0, 0)
        self.client.set_end_effector_gripper.assert_called_once_with(False, False)
        self.client.set_end_effector_suction_cup.assert_called_once_with(False, False)
        self.client.close.assert_called_once_with()
        # the connection is closed last
        self.assertEqual(self.client.method_calls[-1], call.close())


if __name__ == "__main__":
    unittest.main()

"""
Unit-Tests für dobot.py (High-Level-API).

Der Client wird komplett durch einen MagicMock ersetzt. Geprüft wird, ob die API die richtigen
Client-Methoden mit den richtigen Argumenten aufruft. `sleep` wird gepatcht, damit die Tests
nicht warten.
"""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from DobotHub.dobot import Dobot, find_port
from DobotHub.exceptions import DobotConnectionError, DobotError
from DobotHub.types import GP2, GP4, MODE_PTP, Joints, Pose, Position


class DobotTestCase(unittest.TestCase):
    """Basisklasse: Dobot mit gemocktem Client, sleep/time gepatcht."""

    def setUp(self):
        client_patcher = patch("DobotHub.dobot.Client")
        self.client_cls = client_patcher.start()
        self.addCleanup(client_patcher.stop)

        sleep_patcher = patch("DobotHub.dobot.sleep")
        self.sleep = sleep_patcher.start()
        self.addCleanup(sleep_patcher.stop)

        self.bot = Dobot("COM_TEST")
        self.client = self.bot.client
        self.client.reset_mock()          # Aufrufe aus __init__ nicht mitzählen


class TestInit(unittest.TestCase):
    @patch("DobotHub.dobot.Client")
    def test_opens_client_on_port(self, client_cls):
        Dobot("COM7")
        client_cls.assert_called_once_with("COM7")

    @patch("DobotHub.dobot.Client")
    def test_resets_and_starts_queue_first(self, client_cls):
        Dobot("COM7")
        calls = client_cls.return_value.method_calls
        self.assertEqual(calls[:3], [call.stop_queue(True), call.clear_queue(), call.start_queue()])

    @patch("DobotHub.dobot.Client")
    def test_sets_default_motion_params(self, client_cls):
        Dobot("COM7")
        c = client_cls.return_value
        c.set_point_to_point_common_params.assert_called_once_with(100, 100)
        c.set_point_to_point_jump_params.assert_called_once_with(10, 10)
        c.set_continous_trajectory_params.assert_called_once_with(50, 50, 50)


class TestFindPort(unittest.TestCase):
    @patch("DobotHub.dobot.list_ports.comports")
    def test_finds_dobot_by_vid(self, comports):
        comports.return_value = [
            SimpleNamespace(vid=1234, device="COM1"),
            SimpleNamespace(vid=4292, device="COM5"),
        ]
        self.assertEqual(find_port(), "COM5")

    @patch("DobotHub.dobot.list_ports.comports")
    def test_second_vid(self, comports):
        comports.return_value = [SimpleNamespace(vid=6790, device="COM9")]
        self.assertEqual(find_port(), "COM9")

    @patch("DobotHub.dobot.list_ports.comports", return_value=[SimpleNamespace(vid=None, device="COM1")])
    def test_raises_if_no_dobot(self, _):
        with self.assertRaises(DobotConnectionError):
            find_port()

    def test_connection_error_is_dobot_error(self):
        self.assertTrue(issubclass(DobotConnectionError, DobotError))


class TestPose(DobotTestCase):
    def test_get_pose_passes_through(self):
        self.client.get_pose.return_value = (1, 2, 3, 4, 5, 6, 7, 8)
        self.assertEqual(self.bot.get_pose(), (1, 2, 3, 4, 5, 6, 7, 8))

    def test_get_pose_named(self):
        self.client.get_pose.return_value = (200, 0, 50, 10, 1, 45, 30, 9)
        pose = self.bot.get_pose_named()
        self.assertEqual(pose, Pose(Position(200, 0, 50, 10), Joints(1, 45, 30, 9)))
        self.assertEqual(pose.position.z, 50)
        self.assertEqual(pose.joints.j2, 45)

    def test_connected(self):
        self.client.connected.return_value = True
        self.assertTrue(self.bot.connected())


class TestWait(DobotTestCase):
    def test_waits_until_index_passed(self):
        self.client.get_current_queue_index.side_effect = [10, 10, 11]
        self.bot.wait()
        self.client.wait.assert_called_once_with(0)
        self.assertEqual(self.client.get_current_queue_index.call_count, 3)
        self.assertEqual(self.sleep.call_count, 1)

    def test_waits_for_given_index(self):
        self.client.get_current_queue_index.side_effect = [3, 4, 5, 6]
        self.bot.wait(5)
        self.assertEqual(self.client.get_current_queue_index.call_count, 4)


class TestMotion(DobotTestCase):
    def setUp(self):
        super().setUp()
        wait_patcher = patch.object(Dobot, "wait")
        self.wait = wait_patcher.start()
        self.addCleanup(wait_patcher.stop)

    def test_home(self):
        self.bot.home()
        self.client.set_homing_command.assert_called_once_with(0)
        self.wait.assert_called_once()

    def test_home_without_wait(self):
        self.bot.home(wait=False)
        self.wait.assert_not_called()

    def test_set_home(self):
        self.bot.set_home(200, 0, 50)
        self.client.set_homing_parameters.assert_called_once_with(200, 0, 50, 0)

    def test_move_to_passes_mode(self):
        self.bot.move_to(200, 0, 50, 0, mode=MODE_PTP.MOVL_XYZ)
        self.client.set_point_to_point_command.assert_called_once_with(MODE_PTP.MOVL_XYZ, 200, 0, 50, 0)
        self.wait.assert_called_once()

    def test_move_to_without_wait(self):
        self.bot.move_to(200, 0, 50, 0, wait=False)
        self.wait.assert_not_called()

    def test_move_to_relative_uses_cartesian_increment(self):
        self.bot.move_to_relative(0, 0, 10, 0)
        self.client.set_point_to_point_command.assert_called_once_with(MODE_PTP.MOVL_INC, 0, 0, 10, 0)

    def test_slide_to_relative(self):
        self.bot.slide_to_relative(5, 0, 0, 0, wait=False)
        self.client.set_point_to_point_command.assert_called_once_with(MODE_PTP.MOVJ_INC, 5, 0, 0, 0)

    def test_speed(self):
        self.bot.speed(30, 40)
        self.client.set_point_to_point_common_params.assert_called_once_with(30, 40)
        self.client.set_point_to_point_coordinate_params.assert_called_once_with(30, 30, 40, 40)

    def test_follow_path(self):
        self.client.set_continous_trajectory_command.side_effect = [11, 12, 13]
        path = [(200, 0, 50), (210, 0, 50), (210, 10, 50)]
        self.bot.follow_path(path)

        self.client.stop_queue.assert_called_once_with()
        self.assertEqual(self.client.set_continous_trajectory_command.call_args_list,
                         [call(1, x, y, z, 50) for x, y, z in path])
        self.client.start_queue.assert_called_once_with()
        self.wait.assert_called_once_with(13)    # wartet auf den letzten Punkt

    def test_follow_path_relative(self):
        self.bot.follow_path_relative([(10, 0, 0)], wait=False)
        self.client.set_continous_trajectory_command.assert_called_once_with(0, 10, 0, 0, 50)
        self.wait.assert_not_called()

    def test_jog_mapping(self):
        cases = {("x", 1): 1, ("x", -1): 2, ("y", 1): 3, ("y", -1): 4,
                 ("z", 1): 5, ("z", -1): 6, ("r", 1): 7, ("r", -1): 8, ("x", 0): 0}
        for (axis, direction), cmd in cases.items():
            with self.subTest(axis=axis, direction=direction):
                self.client.reset_mock()
                self.bot.jog(axis, direction)
                self.client.set_jog_command.assert_called_once_with(0, cmd)

    def test_jog_invalid_axis(self):
        with self.assertRaises(KeyError):
            self.bot.jog("a", 1)


class TestAlarms(DobotTestCase):
    def test_get_alarms(self):
        self.client.get_alarms_state.return_value = 0
        self.assertEqual(self.bot.get_alarms(), 0)

    def test_clear_alarms(self):
        self.bot.clear_alarms()
        self.client.clear_alarms_state.assert_called_once_with()


class TestEffectors(DobotTestCase):
    def setUp(self):
        super().setUp()
        wait_patcher = patch.object(Dobot, "wait")
        self.wait = wait_patcher.start()
        self.addCleanup(wait_patcher.stop)

    def test_gripper_open(self):
        self.bot.gripper_open()
        self.client.set_end_effector_gripper.assert_called_once_with(True, False)
        self.client.wait.assert_called_once_with(500)
        self.wait.assert_called_once()

    def test_gripper_close(self):
        self.bot.gripper_close(delay=200)
        self.client.set_end_effector_gripper.assert_called_once_with(True, True)
        self.client.wait.assert_called_once_with(200)

    def test_gripper_without_delay_and_wait(self):
        self.bot.gripper_open(wait=False, delay=0)
        self.client.wait.assert_not_called()
        self.wait.assert_not_called()

    def test_gripper_idle(self):
        self.bot.gripper_idle()
        self.client.set_end_effector_gripper.assert_called_once_with(False, False)

    def test_suction_on_off(self):
        self.bot.suction_on()
        self.client.set_end_effector_suction_cup.assert_called_with(True, True)
        self.bot.suction_off()
        self.client.set_end_effector_suction_cup.assert_called_with(False, False)

    def test_laser(self):
        self.bot.laser(True)
        self.client.set_end_effector_laser.assert_called_with(True, True)
        self.bot.laser(False, wait=False)
        self.client.set_end_effector_laser.assert_called_with(True, False)


class TestConveyor(DobotTestCase):
    def test_conveyor(self):
        self.bot.conveyor(50)
        self.client.set_conveyor_speed.assert_called_once_with(50, 0)

    def test_conveyor_stop(self):
        self.bot.conveyor_stop(index=1)
        self.client.set_conveyor_speed.assert_called_once_with(0, 1)

    def test_conveyor_distance_forward(self):
        self.bot.conveyor_distance(100, speed=50)
        self.assertEqual(self.client.set_conveyor_speed.call_args_list, [call(50, 0), call(0, 0)])
        self.sleep.assert_called_once_with(2.0)

    def test_conveyor_distance_backward(self):
        self.bot.conveyor_distance(-25, speed=50)
        self.assertEqual(self.client.set_conveyor_speed.call_args_list, [call(-50, 0), call(0, 0)])
        self.sleep.assert_called_once_with(0.5)


class TestSensors(DobotTestCase):
    def test_ir_enable(self):
        self.bot.ir_enable()
        self.client.set_ir_switch.assert_called_once_with(0, 1, GP4, 1)

    def test_ir_disable(self):
        self.bot.ir_enable(enable=False)
        self.client.set_ir_switch.assert_called_once_with(0, 0, GP4, 1)

    def test_get_ir(self):
        self.client.get_ir_state.return_value = True
        self.assertTrue(self.bot.get_ir())
        self.client.get_ir_state.assert_called_once_with(GP4)

    def test_wait_for_object_detects(self):
        self.client.get_ir_state.side_effect = [False, False, True]
        self.assertTrue(self.bot.wait_for_object())
        self.assertEqual(self.sleep.call_count, 2)

    @patch("DobotHub.dobot.time")
    def test_wait_for_object_timeout(self, time):
        time.side_effect = [0.0, 0.5, 1.5]        # Start, 1. Prüfung, 2. Prüfung (> Timeout)
        self.client.get_ir_state.return_value = False
        self.assertFalse(self.bot.wait_for_object(timeout=1.0))

    def test_color_enable(self):
        self.bot.color_enable()
        self.client.set_color_sensor.assert_called_once_with(0, 1, GP2, 1)

    def test_get_color(self):
        self.client.get_color_sensor.return_value = (1, 0, 0)
        self.assertEqual(self.bot.get_color(), (1, 0, 0))


class TestClose(DobotTestCase):
    def test_close_stops_everything(self):
        self.bot.close()
        self.client.set_conveyor_speed.assert_called_once_with(0, 0)
        self.client.set_end_effector_gripper.assert_called_once_with(False, False)
        self.client.set_end_effector_suction_cup.assert_called_once_with(False, False)
        self.client.close.assert_called_once_with()
        # Verbindung wird erst zum Schluss geschlossen
        self.assertEqual(self.client.method_calls[-1], call.close())


if __name__ == "__main__":
    unittest.main()

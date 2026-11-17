"""
Hardware-Tests Stufe 2: Parameter setzen -> zurücklesen -> Originalwert wiederherstellen.
Der Arm bewegt sich nicht.

Gequeuete Setter werden erst wirksam, wenn der Dobot sie aus der Queue abarbeitet.
Deshalb wird nach jedem Setzen self.bot.wait() aufgerufen.

Ausführen:  pytest --dobot tests/hardware/test_hw_02_params.py
"""

import unittest

import pytest

from tests.hardware.base import HardwareTestCase


class ParamTestCase(HardwareTestCase):
    def roundtrip(self, getter, setter, new_values, set_args=None, places=3):
        """
        Liest den Originalwert, setzt new_values, liest zurück und stellt das Original wieder her.
        set_args: Funktion, die aus einem Werte-Tupel die Argumente für den Setter macht.
        """
        set_args = set_args or (lambda values: list(values))
        original = tuple(getter())
        self.addCleanup(self._restore, setter, set_args(original))

        setter(*set_args(new_values))
        self.bot.wait()
        result = tuple(getter())

        self.assertEqual(len(result), len(new_values))
        for r, e in zip(result, new_values):
            self.assertAlmostEqual(r, e, places=places)

    def _restore(self, setter, args):
        setter(*args)
        self.bot.wait()


class TestPointToPointParams(ParamTestCase):
    def test_common_params(self):
        self.roundtrip(self.client.get_point_to_point_common_params,
                       self.client.set_point_to_point_common_params, (40.0, 30.0))

    def test_coordinate_params(self):
        self.roundtrip(self.client.get_point_to_point_coordinate_params,
                       self.client.set_point_to_point_coordinate_params, (80.0, 70.0, 60.0, 50.0))

    def test_joint_params(self):
        self.roundtrip(self.client.get_point_to_point_joint_params,
                       self.client.set_point_to_point_joint_params,
                       (80.0, 81.0, 82.0, 83.0, 60.0, 61.0, 62.0, 63.0),
                       set_args=lambda v: [list(v[:4]), list(v[4:])])

    def test_jump_params(self):
        self.roundtrip(self.client.get_point_to_point_jump_params,
                       self.client.set_point_to_point_jump_params, (15.0, 20.0))

    def test_jump2_params(self):
        self.roundtrip(self.client.get_point_to_point_jump2_params,
                       self.client.set_point_to_point_jump2_params, (6.0, 7.0, 8.0))


class TestContinuousAndArcParams(ParamTestCase):
    def test_continuous_trajectory_params(self):
        # Getter liefert (max_acc, max_junction_vel, acc, realtime_flag)
        self.roundtrip(self.client.get_continous_trajectory_params,
                       self.client.set_continous_trajectory_params, (40.0, 30.0, 20.0, 0),
                       set_args=lambda v: list(v[:3]))

    def test_arc_params(self):
        self.roundtrip(self.client.get_arc_params,
                       self.client.set_arc_params, (40.0, 30.0, 20.0, 10.0))


class TestJogParams(ParamTestCase):
    def test_common_params(self):
        self.roundtrip(self.client.get_jog_common_params,
                       self.client.set_jog_common_params, (40.0, 30.0))

    # In client.py als "Does not work" markiert -> Hardware-Test klärt das. strict=False, da unklar.
    @pytest.mark.xfail(strict=False, reason="TODO in client.py: set_jog_joint_params funktioniert evtl. nicht")
    def test_joint_params(self):
        self.roundtrip(self.client.get_jog_joint_params,
                       self.client.set_jog_joint_params,
                       (40.0, 41.0, 42.0, 43.0, 30.0, 31.0, 32.0, 33.0),
                       set_args=lambda v: [list(v[:4]), list(v[4:])])

    @pytest.mark.xfail(strict=False, reason="TODO in client.py: set_jog_coordinate_params funktioniert evtl. nicht")
    def test_coordinate_params(self):
        self.roundtrip(self.client.get_jog_coordinate_params,
                       self.client.set_jog_coordinate_params,
                       (40.0, 41.0, 42.0, 43.0, 30.0, 31.0, 32.0, 33.0),
                       set_args=lambda v: [list(v[:4]), list(v[4:])])


class TestHomingParams(ParamTestCase):
    def test_homing_params(self):
        self.roundtrip(self.client.get_homing_paramaters,
                       self.client.set_homing_parameters, (210.0, 5.0, 40.0, 0.0))


class TestSpeedApi(ParamTestCase):
    def test_speed_sets_common_and_coordinate_params(self):
        common = tuple(self.client.get_point_to_point_common_params())
        coord = tuple(self.client.get_point_to_point_coordinate_params())
        self.addCleanup(self._restore, self.client.set_point_to_point_common_params, list(common))
        self.addCleanup(self._restore, self.client.set_point_to_point_coordinate_params, list(coord))

        self.bot.speed(30, 40)
        self.bot.wait()

        self.assertEqual(tuple(self.client.get_point_to_point_common_params()), (30.0, 40.0))
        self.assertEqual(tuple(self.client.get_point_to_point_coordinate_params()), (30.0, 30.0, 40.0, 40.0))


if __name__ == "__main__":
    unittest.main()

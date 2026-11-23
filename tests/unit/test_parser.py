"""
Unit tests for parser.py.

For every message ID it is checked that:
- getter responses (slot 0) are translated correctly into Python values
- setter requests (slot 3) are packed correctly into bytes
- responses to queued commands (slot 2) return the queue index

Known bugs are marked with @pytest.mark.xfail(strict=True). Once a bug is fixed,
the test fails as XPASS -> simply remove the xfail marker.
"""

import struct
import unittest

import pytest

from DobotHub.parser import parsers
from tests.helpers import floats, uint64

F8 = (200.0, 10.0, 50.0, 0.0, 1.0, 45.0, 30.0, -90.0)

# id: (raw bytes from the Dobot, expected Python value)
GETTER_CASES = {
    0: (list(b"SN1234"), "SN1234"),
    1: (list(b"Dobot"), "Dobot"),
    2: ([3, 2, 1], [3, 2, 1]),
    3: ([1], 1),
    4: (list(struct.pack("<L", 123456)), 123456),
    5: (list(struct.pack("<LLL", 1, 2, 3)), (1, 2, 3)),
    10: (floats(*F8), F8),
    13: (floats(100.5), 100.5),
    30: (floats(*F8[:4]), F8[:4]),
    32: (list(struct.pack("<Bf", 1, 0.5)), (1, 0.5)),
    40: ([1], 1),
    41: ([1], True),
    42: ([0], False),
    60: (floats(1.0, 2.0, 3.0), (1.0, 2.0, 3.0)),
    61: ([1, 1], (True, True)),
    62: ([1, 0], (True, False)),
    63: ([1, 1], (True, True)),
    70: (floats(*F8), F8),
    71: (floats(*F8), F8),
    72: (floats(50.0, 60.0), (50.0, 60.0)),
    74: (floats(50.0, 60.0), (50.0, 60.0)),
    80: (floats(*F8), F8),
    81: (floats(*F8[:4]), F8[:4]),
    82: (floats(10.0, 20.0), (10.0, 20.0)),
    83: (floats(50.0, 60.0), (50.0, 60.0)),
    85: (floats(50.0, 60.0), (50.0, 60.0)),
    87: (floats(1.0, 2.0, 3.0), (1.0, 2.0, 3.0)),
    90: (list(struct.pack("<fffB", 1, 2, 3, 1)), (1.0, 2.0, 3.0, 1)),
    100: (floats(*F8[:4]), F8[:4]),
    132: (list(struct.pack("<Bff", 1, 10.0, 50.0)), (1, 10.0, 50.0)),
    134: (list(struct.pack("<BH", 1, 4095)), (1, 4095)),
    138: ([1], (1,)),
    140: (floats(0.5, -0.5), (0.5, -0.5)),
    150: ([1], True),
    151: (list(b"MyWifi"), "MyWifi"),
    152: (list(b"secret"), "secret"),
    157: ([1], True),
    246: (uint64(987654321), 987654321),
}

# Getters with format '<B' * n -> '<B<B...' -> struct.error
BROKEN_GETTERS = {
    20: ([0] * 16, "alarm bitmask"),
    130: ([1, 2], (1, 2)),
    131: ([1, 1], (1, 1)),
    133: ([1, 0], (1, 0)),
    137: ([10, 20, 30], (10, 20, 30)),
    153: ([1, 192, 168, 1, 1], (1, 192, 168, 1, 1)),
    154: ([255, 255, 255, 0], (255, 255, 255, 0)),
    155: ([1, 192, 168, 1], (1, 192, 168, 1)),
    156: ([1, 8, 8, 8], (1, 8, 8, 8)),
}

# id: (Python params, expected bytes)
SETTER_CASES = {
    0: (["SN1"], list(b"SN1\x00")),
    1: (["Dobot"], list(b"Dobot\x00")),
    3: ([1, 0], [1, 0]),
    11: ([1, 10.0, 20.0], list(struct.pack("<Bff", 1, 10, 20))),
    30: ([200, 0, 50, 0], floats(200, 0, 50, 0)),
    31: ([0], floats(0)),
    32: ([1, 0.5], list(struct.pack("<Bf", 1, 0.5))),
    40: ([1], [1]),
    41: ([1], [1]),
    61: ([1, 1], [1, 1]),
    62: ([1, 0], [1, 0]),
    63: ([1, 1], [1, 1]),
    70: (list(F8), floats(*F8)),
    71: (list(F8), floats(*F8)),
    72: ([50, 50], floats(50, 50)),
    73: ([0, 1], [0, 1]),
    74: ([50, 50], floats(50, 50)),
    80: (list(F8), floats(*F8)),
    81: ([100, 100, 100, 100], floats(100, 100, 100, 100)),
    82: ([10, 10], floats(10, 10)),
    83: ([50, 50], floats(50, 50)),
    84: ([1, 200, 0, 50, 0], list(struct.pack("<Bffff", 1, 200, 0, 50, 0))),
    85: ([50, 50], floats(50, 50)),
    86: ([1, 200, 0, 50, 0, 100], list(struct.pack("<Bfffff", 1, 200, 0, 50, 0, 100))),
    87: ([5, 5, 5], floats(5, 5, 5)),
    88: ([1, 200, 0, 50, 0], list(struct.pack("<Bffff", 1, 200, 0, 50, 0))),
    90: ([50, 50, 50, 0], list(struct.pack("<fffB", 50, 50, 50, 0))),
    91: ([1, 200, 0, 50, 50], list(struct.pack("<Bffff", 1, 200, 0, 50, 50))),
    92: ([1, 200, 0, 50, 100], list(struct.pack("<Bffff", 1, 200, 0, 50, 100))),
    100: ([1, 2, 3, 4], floats(1, 2, 3, 4)),
    101: (list(F8), floats(*F8)),
    110: ([500], list(struct.pack("<L", 500))),
    120: ([1, 0, 2, 1000], list(struct.pack("<BBBH", 1, 0, 2, 1000))),
    130: ([1, 2], [1, 2]),
    131: ([1, 1], [1, 1]),
    132: ([1, 10.0, 50.0], list(struct.pack("<Bff", 1, 10, 50))),
    135: ([0, 1, -1000], list(struct.pack("<BBi", 0, 1, -1000))),
    137: ([1, 1, 1], [1, 1, 1]),
    138: ([1, 2, 1], [1, 2, 1]),
    140: ([0.5, -0.5], floats(0.5, -0.5)),
    150: ([1], [1]),
    151: (["MyWifi"], list(b"MyWifi\x00")),
    152: (["secret"], list(b"secret\x00")),
    170: ([5.0], floats(5.0)),
}

BROKEN_SETTERS = {
    # Format '<X' * n -> struct.error
    243: ([1, 10], list(struct.pack("<LL", 1, 10))),
}

BROKEN_WIFI_SETTERS = {
    153: [1, 192, 168, 1, 1],
    154: [255, 255, 255, 0],
    155: [1, 192, 168, 1],
    156: [1, 8, 8, 8],
}


class TestParserTable(unittest.TestCase):
    """Structure and test coverage of the parser dictionary."""

    def test_every_entry_has_four_slots(self):
        """Every entry has four slots, each None or callable."""
        for msg_id, entry in parsers.items():
            with self.subTest(id=msg_id):
                self.assertEqual(len(entry), 4)
                for slot in entry:
                    self.assertTrue(slot is None or callable(slot))

    def test_all_getter_ids_are_covered_by_tests(self):
        """Every ID with a getter parser has a test case."""
        getter_ids = {i for i, p in parsers.items() if p[0] is not None}
        covered = set(GETTER_CASES) | set(BROKEN_GETTERS)
        self.assertEqual(getter_ids - covered, set())


class TestGetterParsers(unittest.TestCase):
    """Getter response parsers (slot 0)."""

    def test_getter_responses(self):
        """Raw response bytes are translated into the expected Python values."""
        for msg_id, (raw, expected) in GETTER_CASES.items():
            with self.subTest(id=msg_id):
                result = parsers[msg_id][0](raw)
                if isinstance(expected, tuple) and any(isinstance(v, float) for v in expected):
                    self.assertEqual(len(result), len(expected))
                    for r, e in zip(result, expected):
                        self.assertAlmostEqual(r, e, places=5)
                else:
                    self.assertEqual(result, expected)

    def test_getter_with_wrong_length_raises(self):
        """A response with the wrong length raises struct.error."""
        with self.assertRaises(struct.error):
            parsers[10][0](floats(1, 2, 3))   # pose needs 8 floats


@pytest.mark.xfail(strict=True, raises=struct.error, reason="Bug in parser.py: format '<B' * n instead of '<' + 'B' * n")
class TestBrokenByteGetters(unittest.TestCase):
    """Getters affected by the '<B' * n format bug."""

    def test_alarm_state(self):
        """ID 20: alarm state can be parsed."""
        parsers[20][0](BROKEN_GETTERS[20][0])

    def test_io_multiplexing(self):
        """ID 130: IO multiplexing can be parsed."""
        raw, expected = BROKEN_GETTERS[130]
        self.assertEqual(parsers[130][0](raw), expected)

    def test_io_do(self):
        """ID 131: digital outputs can be parsed."""
        raw, expected = BROKEN_GETTERS[131]
        self.assertEqual(parsers[131][0](raw), expected)

    def test_io_di(self):
        """ID 133: digital inputs can be parsed."""
        raw, expected = BROKEN_GETTERS[133]
        self.assertEqual(parsers[133][0](raw), expected)

    def test_color_sensor(self):
        """ID 137: color sensor values can be parsed."""
        raw, expected = BROKEN_GETTERS[137]
        self.assertEqual(parsers[137][0](raw), expected)

    def test_wifi_address(self):
        """ID 153: WiFi address can be parsed."""
        raw, expected = BROKEN_GETTERS[153]
        self.assertEqual(parsers[153][0](raw), expected)


class TestSetterParsers(unittest.TestCase):
    """Setter request parsers (slot 3)."""

    def test_setter_requests(self):
        """Python params are packed into the expected bytes."""
        for msg_id, (params, expected) in SETTER_CASES.items():
            with self.subTest(id=msg_id):
                self.assertEqual(parsers[msg_id][3](params), expected)

    def test_setter_output_is_list_of_bytes(self):
        """Every setter parser returns a list of byte values."""
        for msg_id, (params, _) in SETTER_CASES.items():
            with self.subTest(id=msg_id):
                result = parsers[msg_id][3](params)
                self.assertIsInstance(result, list)
                self.assertTrue(all(0 <= b <= 255 for b in result))

    @pytest.mark.xfail(strict=True, raises=struct.error,
                       reason="Bug: ID 60 packs 4 floats, but set_end_effector_params passes 3 (x, y, z)")
    def test_end_effector_params(self):
        """ID 60: end effector offsets (x, y, z) can be packed."""
        self.assertEqual(parsers[60][3]([1.0, 2.0, 3.0]), floats(1, 2, 3))

    @pytest.mark.xfail(strict=True, raises=struct.error, reason="Bug in parser.py: format '<B' * n")
    def test_wifi_setters(self):
        """IDs 153-156: WiFi network settings can be packed."""
        for msg_id, params in BROKEN_WIFI_SETTERS.items():
            self.assertEqual(parsers[msg_id][3](params), params)

    @pytest.mark.xfail(strict=True, raises=struct.error, reason="Bug in parser.py: ID 243 format '<L' * 2")
    def test_start_queue_download(self):
        """ID 243: queue download params can be packed."""
        params, expected = BROKEN_SETTERS[243]
        self.assertEqual(parsers[243][3](params), expected)


class TestQueuedResponseParsers(unittest.TestCase):
    """Queued response parsers (slot 2)."""

    def test_queued_responses_return_queue_index(self):
        """Every queued response parser returns the uint64 queue index."""
        for msg_id, entry in parsers.items():
            if entry[2] is None:
                continue
            with self.subTest(id=msg_id):
                self.assertEqual(entry[2](uint64(4711)), 4711)


if __name__ == "__main__":
    unittest.main()

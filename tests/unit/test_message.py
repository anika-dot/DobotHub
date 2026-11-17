"""Unit-Tests für message.py: Checksumme, Paket bauen, Paket lesen."""

import struct
import unittest

from DobotHub.message import Message
from tests.helpers import FakeSerial, decode, floats, frame, uint64


class TestChecksum(unittest.TestCase):
    def test_checksum_is_twos_complement(self):
        # get_pose: ID 10, Control 0 -> 256 - 10 = 246
        self.assertEqual(Message.calculate_checksum([10, 0]), 0xF6)

    def test_checksum_of_zero_sum_is_zero(self):
        self.assertEqual(Message.calculate_checksum([0, 0]), 0)
        self.assertEqual(Message.calculate_checksum([128, 128]), 0)

    def test_checksum_is_always_a_byte(self):
        for payload in ([255] * 50, [1], list(range(256))):
            with self.subTest(payload=payload[:3]):
                self.assertIn(Message.calculate_checksum(payload), range(256))

    def test_verify_checksum(self):
        payload = [84, 3] + floats(200, 0, 50, 0)
        good = Message.calculate_checksum(payload)
        self.assertTrue(Message.verify_checksum(payload, good))
        self.assertFalse(Message.verify_checksum(payload, (good + 1) % 256))


class TestPackage(unittest.TestCase):
    def test_getter_without_params(self):
        msg = Message([0xAA, 0xAA], 2, 10, False, False, [], direction="out")
        self.assertEqual(msg.package(), bytes([0xAA, 0xAA, 0x02, 0x0A, 0x00, 0xF6]))

    def test_control_byte_bits(self):
        cases = {(False, False): 0, (True, False): 1, (False, True): 2, (True, True): 3}
        for (rw, queued), control in cases.items():
            with self.subTest(rw=rw, queued=queued):
                msg = Message([0xAA, 0xAA], 2, 245, rw, queued, [], direction="out")
                self.assertEqual(msg.package()[4], control)

    def test_queued_setter_with_params(self):
        msg = Message([0xAA, 0xAA], 2, 84, True, True, [1, 200.0, 0.0, 50.0, 0.0], direction="out")
        data = msg.package()

        self.assertEqual(data, frame(84, list(struct.pack("<Bffff", 1, 200, 0, 50, 0)), rw=True, queued=True))
        self.assertEqual(data[2], 2 + 17)       # Länge = ID + Control + 17 Byte Params

    def test_package_matches_reference_frame(self):
        msg = Message([0xAA, 0xAA], 2, 31, True, True, [0], direction="out")
        f = decode(msg.package())
        self.assertEqual((f.id, f.rw, f.queued), (31, True, True))
        self.assertEqual(f.params, floats(0))

    def test_package_updates_length(self):
        msg = Message([0xAA, 0xAA], 99, 1, True, False, ["Dobot"], direction="out")
        msg.package()
        self.assertEqual(msg.length, 2 + len("Dobot") + 1)   # inkl. Null-Terminator


class TestParse(unittest.TestCase):
    def test_parse_valid_getter_response(self):
        data = frame(10, floats(200, 0, 50, 0, 0, 45, 45, 0))
        msg = Message.parse(data)

        self.assertIsNotNone(msg)
        self.assertEqual(msg.id, 10)
        self.assertFalse(msg.rw)
        self.assertFalse(msg.is_queued)
        self.assertEqual(msg.params, (200, 0, 50, 0, 0, 45, 45, 0))

    def test_parse_queued_response_returns_queue_index(self):
        msg = Message.parse(frame(84, uint64(1234), rw=True, queued=True))
        self.assertTrue(msg.rw)
        self.assertTrue(msg.is_queued)
        self.assertEqual(msg.params, 1234)

    def test_parse_rejects_bad_checksum(self):
        data = bytearray(frame(10, floats(*[0] * 8)))
        data[-1] = (data[-1] + 1) % 256
        self.assertIsNone(Message.parse(bytes(data)))

    def test_package_and_parse_roundtrip(self):
        out = Message([0xAA, 0xAA], 2, 1, True, False, ["Dobot"], direction="out")
        back = Message.parse(out.package())
        self.assertEqual(back.raw_params, list(b"Dobot\x00"))


class TestRead(unittest.TestCase):
    def test_read_complete_frame(self):
        fake = FakeSerial()
        fake.queue(frame(246, uint64(42), rw=True))
        msg = Message.read(fake)
        self.assertEqual(msg.params, 42)

    def test_read_consumes_exactly_one_frame(self):
        fake = FakeSerial()
        fake.queue(frame(246, uint64(1)) + frame(246, uint64(2)))
        self.assertEqual(Message.read(fake).params, 1)
        self.assertEqual(Message.read(fake).params, 2)

    def test_read_wrong_header_returns_none(self):
        fake = FakeSerial()
        fake.queue(b"\x00\x00\x02\x0a\x00\xf6")
        self.assertIsNone(Message.read(fake))

    def test_read_timeout_returns_none(self):
        # Leerer Puffer verhält sich wie ein serieller Timeout (read liefert b"")
        self.assertIsNone(Message.read(FakeSerial()))


if __name__ == "__main__":
    unittest.main()

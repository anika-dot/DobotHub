"""Unit tests for message.py: checksum, building packets, reading packets."""

import struct
import unittest

from DobotHub.message import Message
from tests.helpers import FakeSerial, decode, floats, frame, uint64


class TestChecksum(unittest.TestCase):
    """Checksum calculation and verification."""

    def test_checksum_is_twos_complement(self):
        """The checksum is the two's complement of the payload sum."""
        # get_pose: ID 10, control 0 -> 256 - 10 = 246
        self.assertEqual(Message.calculate_checksum([10, 0]), 0xF6)

    def test_checksum_of_zero_sum_is_zero(self):
        """A payload sum divisible by 256 gives checksum 0."""
        self.assertEqual(Message.calculate_checksum([0, 0]), 0)
        self.assertEqual(Message.calculate_checksum([128, 128]), 0)

    def test_checksum_is_always_a_byte(self):
        """The checksum always fits into one byte."""
        for payload in ([255] * 50, [1], list(range(256))):
            with self.subTest(payload=payload[:3]):
                self.assertIn(Message.calculate_checksum(payload), range(256))

    def test_verify_checksum(self):
        """verify_checksum() accepts the correct and rejects a wrong checksum."""
        payload = [84, 3] + floats(200, 0, 50, 0)
        good = Message.calculate_checksum(payload)
        self.assertTrue(Message.verify_checksum(payload, good))
        self.assertFalse(Message.verify_checksum(payload, (good + 1) % 256))


class TestPackage(unittest.TestCase):
    """Building outgoing packets with package()."""

    def test_getter_without_params(self):
        """A getter without params produces the reference frame."""
        msg = Message([0xAA, 0xAA], 2, 10, False, False, [], direction="out")
        self.assertEqual(msg.package(), bytes([0xAA, 0xAA, 0x02, 0x0A, 0x00, 0xF6]))

    def test_control_byte_bits(self):
        """rw sets bit 0 and is_queued sets bit 1 of the control byte."""
        cases = {(False, False): 0, (True, False): 1, (False, True): 2, (True, True): 3}
        for (rw, queued), control in cases.items():
            with self.subTest(rw=rw, queued=queued):
                msg = Message([0xAA, 0xAA], 2, 245, rw, queued, [], direction="out")
                self.assertEqual(msg.package()[4], control)

    def test_queued_setter_with_params(self):
        """A queued PTP command contains the packed params and the correct length."""
        msg = Message([0xAA, 0xAA], 2, 84, True, True, [1, 200.0, 0.0, 50.0, 0.0], direction="out")
        data = msg.package()

        self.assertEqual(data, frame(84, list(struct.pack("<Bffff", 1, 200, 0, 50, 0)), rw=True, queued=True))
        self.assertEqual(data[2], 2 + 17)       # length = ID + control + 17 bytes params

    def test_package_matches_reference_frame(self):
        """The homing command decodes to the expected ID, flags and params."""
        msg = Message([0xAA, 0xAA], 2, 31, True, True, [0], direction="out")
        f = decode(msg.package())
        self.assertEqual((f.id, f.rw, f.queued), (31, True, True))
        self.assertEqual(f.params, floats(0))

    def test_package_updates_length(self):
        """package() recalculates the length field."""
        msg = Message([0xAA, 0xAA], 99, 1, True, False, ["Dobot"], direction="out")
        msg.package()
        self.assertEqual(msg.length, 2 + len("Dobot") + 1)   # incl. null terminator


class TestParse(unittest.TestCase):
    """Parsing incoming packets with parse()."""

    def test_parse_valid_getter_response(self):
        """A valid pose response is parsed into eight values."""
        data = frame(10, floats(200, 0, 50, 0, 0, 45, 45, 0))
        msg = Message.parse(data)

        self.assertIsNotNone(msg)
        self.assertEqual(msg.id, 10)
        self.assertFalse(msg.rw)
        self.assertFalse(msg.is_queued)
        self.assertEqual(msg.params, (200, 0, 50, 0, 0, 45, 45, 0))

    def test_parse_queued_response_returns_queue_index(self):
        """A queued response is parsed into the queue index."""
        msg = Message.parse(frame(84, uint64(1234), rw=True, queued=True))
        self.assertTrue(msg.rw)
        self.assertTrue(msg.is_queued)
        self.assertEqual(msg.params, 1234)

    def test_parse_rejects_bad_checksum(self):
        """A packet with a wrong checksum returns None."""
        data = bytearray(frame(10, floats(*[0] * 8)))
        data[-1] = (data[-1] + 1) % 256
        self.assertIsNone(Message.parse(bytes(data)))

    def test_package_and_parse_roundtrip(self):
        """A packed message can be parsed back to the same raw params."""
        out = Message([0xAA, 0xAA], 2, 1, True, False, ["Dobot"], direction="out")
        back = Message.parse(out.package())
        self.assertEqual(back.raw_params, list(b"Dobot\x00"))


class TestRead(unittest.TestCase):
    """Reading packets from a serial port with read()."""

    def test_read_complete_frame(self):
        """A complete frame is read and parsed."""
        fake = FakeSerial()
        fake.queue(frame(246, uint64(42), rw=True))
        msg = Message.read(fake)
        self.assertEqual(msg.params, 42)

    def test_read_consumes_exactly_one_frame(self):
        """read() consumes exactly one frame from the buffer."""
        fake = FakeSerial()
        fake.queue(frame(246, uint64(1)) + frame(246, uint64(2)))
        self.assertEqual(Message.read(fake).params, 1)
        self.assertEqual(Message.read(fake).params, 2)

    def test_read_wrong_header_returns_none(self):
        """A frame with a wrong header returns None."""
        fake = FakeSerial()
        fake.queue(b"\x00\x00\x02\x0a\x00\xf6")
        self.assertIsNone(Message.read(fake))

    def test_read_timeout_returns_none(self):
        """An empty buffer (serial timeout) returns None."""
        # An empty buffer behaves like a serial timeout (read returns b"")
        self.assertIsNone(Message.read(FakeSerial()))


if __name__ == "__main__":
    unittest.main()

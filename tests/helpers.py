"""
Helpers for tests without Dobot.

frame(...)      builds a complete protocol packet (header, length, ID, control, params, checksum)
decode(...)     splits a packet back into its components
FakeSerial      replaces serial.Serial; records sent bytes and provides prepared responses
"""

import struct
from collections import namedtuple

Frame = namedtuple("Frame", "id rw queued params")


def checksum(payload):
    """
    Calculates the checksum for a payload (list of bytes) according to the Dobot protocol.
    """
    return (256 - sum(payload) % 256) % 256


def frame(id, params=(), rw=False, queued=False):
    """
    Creates a complete protocol packet (header, length, ID, control, params, checksum).
    """
    params = list(params)
    control = (int(queued) << 1) | int(rw)
    payload = [id, control] + params
    return bytes([0xAA, 0xAA, len(payload)] + payload + [checksum(payload)])


def decode(data):
    """
    Splits a packet back into its components and checks the header, length, and checksum.
    """
    data = bytes(data)
    assert data[:2] == b"\xaa\xaa", f"false Header: {data[:2]!r}"
    length = data[2]
    payload = list(data[3:3 + length])
    assert len(data) == 3 + length + 1, f"false Length: {len(data) - 3 - length}"
    assert checksum(payload) == data[-1], f"false Checksum: {data[-1]}"
    control = payload[1]
    return Frame(payload[0], bool(control & 1), bool(control & 2), payload[2:])


def floats(*values):
    """
    Little-endian float32 as a list of bytes (as sent by the Dobot).
    """
    return list(struct.pack("<" + "f" * len(values), *values))


def uint64(value):
    """
    Queue-Index as a list of bytes (uint64, little-endian). Used for queued commands.
    """
    return list(struct.pack("<Q", value))


class FakeSerial:
    """
    Minimal replacement for serial.Serial.

    Answers can be provided in two ways:
    - fake.queue(bytes)          -> will be delivered on the next read()
    - fake.responses[id] = [...] -> automatic response to any request with this ID
      (same ID and control bits as the request; if not present: queue index for queued
        commands, otherwise empty params)
    """

    def __init__(self):
        self.written = b""
        self.requests = []          # all sent requests (decoded)
        self.responses = {}
        self.queue_index = 1
        self.auto_respond = True
        self.is_open = True
        self._rx = bytearray()

    # --- Test  Control
    def queue(self, data):
        """
        Queues bytes to be returned by the next read() call.
        """
        self._rx.extend(data)

    @property
    def last(self):
        """
        Returns the last sent request (decoded).
        """
        return self.requests[-1]

    # --- serial.Serial-API
    def write(self, data):
        """
        Records the sent bytes, decodes the request, and queues a response if auto_respond is True.
        """
        self.written += bytes(data)
        request = decode(data)
        self.requests.append(request)
        if self.auto_respond and not self._rx:
            self._rx.extend(self._respond(request))
        return len(data)

    def _respond(self, request):
        """
        Returns a response for the given request (as bytes).
        """
        if request.id in self.responses:
            params = self.responses[request.id]
        elif request.queued:
            params = uint64(self.queue_index)
            self.queue_index += 1
        else:
            params = []
        return frame(request.id, params, rw=request.rw, queued=request.queued)

    def read(self, size=1):
        """
        Returns the next `size` bytes from the queue (or less if not enough data is available).
        """
        chunk = bytes(self._rx[:size])
        del self._rx[:size]
        return chunk

    def flush(self):
        """
        Does nothing (for compatibility with serial.Serial).
        """
        pass

    def isOpen(self):
        """
        Returns True if the serial port is open (for compatibility with serial.Serial).
        """
        return self.is_open

    def close(self):
        """
        Closes the serial port (for compatibility with serial.Serial).
        """
        self.is_open = False

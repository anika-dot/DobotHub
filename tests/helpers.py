"""
Hilfsmittel für Tests ohne Dobot.

frame(...)      baut ein vollständiges Protokoll-Paket (Header, Länge, ID, Control, Params, Checksumme)
decode(...)     zerlegt ein Paket wieder in seine Bestandteile
FakeSerial      ersetzt serial.Serial; zeichnet gesendete Bytes auf und liefert vorbereitete Antworten
"""

import struct
from collections import namedtuple

Frame = namedtuple("Frame", "id rw queued params")


def checksum(payload):
    return (256 - sum(payload) % 256) % 256


def frame(id, params=(), rw=False, queued=False):
    """Baut ein Paket genau so, wie es laut Dobot-Protokoll auf der Leitung liegt."""
    params = list(params)
    control = (int(queued) << 1) | int(rw)
    payload = [id, control] + params
    return bytes([0xAA, 0xAA, len(payload)] + payload + [checksum(payload)])


def decode(data):
    """Zerlegt ein Paket in (id, rw, queued, params) und prüft dabei Header, Länge und Checksumme."""
    data = bytes(data)
    assert data[:2] == b"\xaa\xaa", f"falscher Header: {data[:2]!r}"
    length = data[2]
    payload = list(data[3:3 + length])
    assert len(data) == 3 + length + 1, "Länge stimmt nicht mit Paketgrösse überein"
    assert checksum(payload) == data[-1], "falsche Checksumme"
    control = payload[1]
    return Frame(payload[0], bool(control & 1), bool(control & 2), payload[2:])


def floats(*values):
    """Little-endian float32 als Byte-Liste (wie der Dobot sie sendet)."""
    return list(struct.pack("<" + "f" * len(values), *values))


def uint64(value):
    """Queue-Index als Byte-Liste (uint64, little-endian)."""
    return list(struct.pack("<Q", value))


class FakeSerial:
    """
    Minimaler Ersatz für serial.Serial.

    Antworten können auf zwei Arten bereitgestellt werden:
    - fake.queue(bytes)          -> wird beim nächsten read() geliefert
    - fake.responses[id] = [...] -> automatische Antwort auf jede Anfrage mit dieser ID
      (gleiche ID und Control-Bits wie die Anfrage; ohne Eintrag: Queue-Index bei
      gequeueten Befehlen, sonst leere Params)
    """

    def __init__(self):
        self.written = b""
        self.requests = []          # alle gesendeten Pakete, decodiert
        self.responses = {}
        self.queue_index = 1
        self.auto_respond = True
        self.is_open = True
        self._rx = bytearray()

    # --- Teststeuerung ---
    def queue(self, data):
        self._rx.extend(data)

    @property
    def last(self):
        return self.requests[-1]

    # --- serial.Serial-API ---
    def write(self, data):
        self.written += bytes(data)
        request = decode(data)
        self.requests.append(request)
        if self.auto_respond and not self._rx:
            self._rx.extend(self._respond(request))
        return len(data)

    def _respond(self, request):
        if request.id in self.responses:
            params = self.responses[request.id]
        elif request.queued:
            params = uint64(self.queue_index)
            self.queue_index += 1
        else:
            params = []
        return frame(request.id, params, rw=request.rw, queued=request.queued)

    def read(self, size=1):
        chunk = bytes(self._rx[:size])
        del self._rx[:size]
        return chunk

    def flush(self):
        pass

    def isOpen(self):
        return self.is_open

    def close(self):
        self.is_open = False

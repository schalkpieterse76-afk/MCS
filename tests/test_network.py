"""Tests for network frame building and parsing."""
import struct
from mcs_cvor.network.tcp_client import build_frame, parse_frame, STX, ETX, _checksum


def test_build_frame_structure():
    frame = build_frame(0x10)
    assert frame[0] == STX
    assert frame[-2] == ETX
    # cmd byte
    assert frame[1] == 0x10
    # length bytes (0 payload)
    length = struct.unpack(">H", frame[2:4])[0]
    assert length == 0


def test_build_frame_with_payload():
    payload = b"\x01\x02\x03"
    frame = build_frame(0x20, payload)
    assert frame[0] == STX
    assert frame[-2] == ETX
    length = struct.unpack(">H", frame[2:4])[0]
    assert length == 3


def test_frame_roundtrip():
    payload = b"\xAB\xCD\xEF"
    frame = build_frame(0x10, payload)
    parsed = parse_frame(frame)
    assert parsed is not None
    assert parsed["cmd"] == 0x10
    assert parsed["payload"] == payload


def test_parse_frame_bad_checksum():
    frame = bytearray(build_frame(0x10, b"\x01"))
    # Corrupt checksum
    frame[-1] ^= 0xFF
    result = parse_frame(bytes(frame))
    assert result is None


def test_parse_frame_too_short():
    result = parse_frame(b"\x02\x03")
    assert result is None


def test_parse_frame_missing_stx():
    frame = build_frame(0x10)
    bad = b"\x00" + frame[1:]
    result = parse_frame(bad)
    assert result is None


def test_checksum_empty():
    assert _checksum(b"") == 0


def test_checksum_xor():
    data = bytes([0x10, 0x00, 0x00])
    assert _checksum(data) == 0x10

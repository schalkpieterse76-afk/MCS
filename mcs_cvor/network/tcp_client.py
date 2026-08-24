"""Thales CVOR TCP client with async support."""
import asyncio
import struct
from typing import Optional

STX = 0x02
ETX = 0x03

STATUS_MAP = {0x00: "INACTIVE", 0x01: "ACTIVE", 0x02: "STANDBY", 0x03: "FAULT", 0x04: "MAINTENANCE"}


def _checksum(data: bytes) -> int:
    cs = 0
    for b in data:
        cs ^= b
    return cs & 0xFF


def build_frame(cmd: int, payload: bytes = b"") -> bytes:
    length = len(payload)
    frame_body = bytes([cmd]) + struct.pack(">H", length) + payload
    cs = _checksum(frame_body)
    return bytes([STX]) + frame_body + bytes([ETX, cs])


def parse_frame(data: bytes) -> Optional[dict]:
    if len(data) < 5:
        return None
    if data[0] != STX or data[-2] != ETX:
        return None
    frame_body = data[1:-2]
    cs_received = data[-1]
    cs_calc = _checksum(frame_body)
    if cs_received != cs_calc:
        return None
    cmd = frame_body[0]
    length = struct.unpack(">H", frame_body[1:3])[0]
    payload = frame_body[3:3 + length]
    return {"cmd": cmd, "payload": payload}


class CVORTCPClient:
    def __init__(self, host: str, port: int = 5000, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    async def _send_receive(self, frame: bytes) -> Optional[bytes]:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=self.timeout
            )
            writer.write(frame)
            await writer.drain()
            data = await asyncio.wait_for(reader.read(1024), timeout=self.timeout)
            writer.close()
            await writer.wait_closed()
            return data
        except Exception:
            return None

    async def get_status(self) -> Optional[dict]:
        frame = build_frame(0x10)
        response = await self._send_receive(frame)
        if not response:
            return None
        parsed = parse_frame(response)
        if not parsed or len(parsed["payload"]) < 6:
            return None
        payload = parsed["payload"]
        status_byte = payload[0]
        alarm_word = struct.unpack(">H", payload[1:3])[0]
        freq = struct.unpack(">H", payload[3:5])[0] / 10.0
        power = payload[5]
        vswr = payload[6] / 10.0 if len(payload) > 6 else 0.0
        return {
            "status": STATUS_MAP.get(status_byte, "INACTIVE"),
            "alarm_word": alarm_word,
            "frequency": freq,
            "power_w": power,
            "vswr": vswr,
        }

    async def set_parameter(self, param_id: int, value_bytes: bytes) -> bool:
        payload = bytes([param_id]) + value_bytes
        frame = build_frame(0x20, payload)
        response = await self._send_receive(frame)
        if not response:
            return False
        parsed = parse_frame(response)
        return parsed is not None and parsed["cmd"] == 0x21

    async def reset_system(self) -> bool:
        frame = build_frame(0x30)
        response = await self._send_receive(frame)
        if not response:
            return False
        parsed = parse_frame(response)
        return parsed is not None and parsed["cmd"] == 0x31

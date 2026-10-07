"""BWT AQA Perla serial protocol primitives.

The protocol information is inferred from the supplied IP-Symcon scripts.
Frames use this layout::

    0x0D | command | payload length | payload | checksum | 0x0A

The checksum is the low eight bits of the sum of every preceding frame byte.
Multi-byte values in the supplied scripts are little-endian.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum

START_BYTE = 0x0D
END_BYTE = 0x0A


class Command(IntEnum):
    """Known read commands."""

    DEVICE_TYPE = 0x01
    REMAINING_CAPACITY_COLUMN_1 = 0x02
    REMAINING_CAPACITY_COLUMN_2 = 0x03
    REGENERATION_STEP = 0x04
    PEAK_FLOW_TODAY = 0x05
    PEAK_FLOW_24H = 0x06
    PEAK_FLOW_SINCE_COMMISSIONING = 0x07
    WATER_CONSUMPTION_24H = 0x08
    TOTAL_WATER_CONSUMPTION = 0x10
    REGENERATION_COUNT = 0x11
    REGENERATION_COUNT_SINCE_SERVICE = 0x12
    TOTAL_SALT_CONSUMPTION = 0x13
    REGENERANT_SAVING = 0x14
    COMMISSIONING_DATE = 0x15
    SOFTWARE_VERSION = 0x19
    NOMINAL_CAPACITY_COLUMN_1 = 0x25
    NOMINAL_CAPACITY_COLUMN_2 = 0x26


class ValueType(Enum):
    """Supported response payload encodings."""

    UNSIGNED_LITTLE_ENDIAN = "uint_le"
    ASCII = "ascii"


@dataclass(frozen=True, slots=True)
class QuerySpec:
    """Description of a value exposed by the device."""

    key: str
    command: Command
    expected_length: int | None
    scale: float = 1.0
    optional: bool = False
    value_type: ValueType = ValueType.UNSIGNED_LITTLE_ENDIAN


QUERY_SPECS: tuple[QuerySpec, ...] = (
    QuerySpec("device_type", Command.DEVICE_TYPE, 1, optional=True),
    QuerySpec("peak_flow_today", Command.PEAK_FLOW_TODAY, 2, optional=True),
    QuerySpec("peak_flow_24h", Command.PEAK_FLOW_24H, 2, optional=True),
    QuerySpec(
        "peak_flow_since_commissioning",
        Command.PEAK_FLOW_SINCE_COMMISSIONING,
        2,
        optional=True,
    ),
    QuerySpec("water_consumption_24h", Command.WATER_CONSUMPTION_24H, 2),
    QuerySpec("total_water_consumption", Command.TOTAL_WATER_CONSUMPTION, 4),
    QuerySpec("total_salt_consumption", Command.TOTAL_SALT_CONSUMPTION, 4, 0.001),
    QuerySpec("nominal_capacity_column_1", Command.NOMINAL_CAPACITY_COLUMN_1, 2),
    QuerySpec("nominal_capacity_column_2", Command.NOMINAL_CAPACITY_COLUMN_2, 2),
    QuerySpec("remaining_capacity_column_1", Command.REMAINING_CAPACITY_COLUMN_1, 2),
    QuerySpec("remaining_capacity_column_2", Command.REMAINING_CAPACITY_COLUMN_2, 2),
    QuerySpec("regeneration_count", Command.REGENERATION_COUNT, 2),
    QuerySpec(
        "regeneration_count_since_service",
        Command.REGENERATION_COUNT_SINCE_SERVICE,
        2,
        optional=True,
    ),
    QuerySpec("regeneration_step", Command.REGENERATION_STEP, 1),
    # The supplied script queries command 0x14 but never parses its response.
    # A published capture documents two bytes; it remains optional so an older
    # or different firmware cannot make all other readings unavailable.
    QuerySpec("regenerant_saving", Command.REGENERANT_SAVING, 2, optional=True),
    QuerySpec(
        "commissioning_date",
        Command.COMMISSIONING_DATE,
        None,
        optional=True,
        value_type=ValueType.ASCII,
    ),
    QuerySpec(
        "software_version",
        Command.SOFTWARE_VERSION,
        None,
        optional=True,
        value_type=ValueType.ASCII,
    ),
)


class BwtProtocolError(Exception):
    """Base exception for malformed BWT data."""


class BwtChecksumError(BwtProtocolError):
    """Raised when a frame checksum is invalid."""


class BwtResponseError(BwtProtocolError):
    """Raised when a response does not match its request."""


def checksum(data: bytes) -> int:
    """Return the protocol's additive 8-bit checksum."""

    return sum(data) & 0xFF


def build_query(command: int | Command) -> bytes:
    """Build a zero-payload read request."""

    body = bytes((START_BYTE, int(command), 0))
    return body + bytes((checksum(body), END_BYTE))


def build_frame(command: int | Command, payload: bytes) -> bytes:
    """Build a complete frame, primarily useful for tests and captures."""

    if len(payload) > 255:
        raise ValueError("Payload is too long")
    body = bytes((START_BYTE, int(command), len(payload))) + payload
    return body + bytes((checksum(body), END_BYTE))


def parse_frame(frame: bytes, expected_command: int | Command | None = None) -> bytes:
    """Validate a complete frame and return its payload."""

    if len(frame) < 5:
        raise BwtProtocolError("Frame is shorter than the minimum length")
    if frame[0] != START_BYTE or frame[-1] != END_BYTE:
        raise BwtProtocolError("Invalid frame boundary")

    payload_length = frame[2]
    if len(frame) != payload_length + 5:
        raise BwtProtocolError(
            f"Frame length mismatch: header says {payload_length}, got {len(frame) - 5}"
        )
    if checksum(frame[:-2]) != frame[-2]:
        raise BwtChecksumError("Invalid frame checksum")
    if expected_command is not None and frame[1] != int(expected_command):
        raise BwtResponseError(
            f"Expected command 0x{int(expected_command):02X}, got 0x{frame[1]:02X}"
        )
    return frame[3:-2]


def decode_value(payload: bytes, spec: QuerySpec) -> int | float | str:
    """Decode one numeric or textual device value."""

    if spec.expected_length is not None and len(payload) != spec.expected_length:
        raise BwtResponseError(
            f"Command 0x{spec.command:02X} returned {len(payload)} bytes; "
            f"expected {spec.expected_length}"
        )
    if not payload:
        raise BwtResponseError(f"Command 0x{spec.command:02X} returned no data")
    if spec.value_type is ValueType.ASCII:
        try:
            # Device texts observed in SoftControl are ASCII and may include
            # trailing protocol/control characters.
            return payload.decode("ascii").strip("\x00\x03\r\n ")
        except UnicodeDecodeError as err:
            raise BwtResponseError(
                f"Command 0x{spec.command:02X} returned invalid ASCII"
            ) from err
    raw = int.from_bytes(payload, byteorder="little", signed=False)
    return raw if spec.scale == 1.0 else raw * spec.scale


def normalize_regeneration_step(raw_value: int) -> int:
    """Return the SoftControl 1.5 lookup index for a regeneration byte."""

    return raw_value & 0x7F


def split_software_version(value: str) -> tuple[str, str | None]:
    """Split SoftControl's electronics#control-panel version response."""

    cleaned = value.removeprefix("Version:").strip()
    electronics, separator, control_panel = cleaned.partition("#")
    return electronics.strip(), control_panel.strip() if separator else None

"""Tests for the inferred BWT AQA Perla wire protocol."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

PROTOCOL_PATH = (
    Path(__file__).parents[1] / "custom_components" / "bwt_aqa_perla" / "protocol.py"
)
SPEC = importlib.util.spec_from_file_location("bwt_protocol_for_test", PROTOCOL_PATH)
assert SPEC is not None and SPEC.loader is not None
protocol = importlib.util.module_from_spec(SPEC)
# Dataclasses look up their module while decorating the class.
import sys

sys.modules[SPEC.name] = protocol
SPEC.loader.exec_module(protocol)


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        (0x01, bytes.fromhex("0D 01 00 0E 0A")),
        (0x05, bytes.fromhex("0D 05 00 12 0A")),
        (0x06, bytes.fromhex("0D 06 00 13 0A")),
        (0x07, bytes.fromhex("0D 07 00 14 0A")),
        (0x08, bytes.fromhex("0D 08 00 15 0A")),
        (0x10, bytes.fromhex("0D 10 00 1D 0A")),
        (0x13, bytes.fromhex("0D 13 00 20 0A")),
        (0x25, bytes.fromhex("0D 25 00 32 0A")),
        (0x26, bytes.fromhex("0D 26 00 33 0A")),
        (0x02, bytes.fromhex("0D 02 00 0F 0A")),
        (0x03, bytes.fromhex("0D 03 00 10 0A")),
        (0x11, bytes.fromhex("0D 11 00 1E 0A")),
        (0x12, bytes.fromhex("0D 12 00 1F 0A")),
        (0x04, bytes.fromhex("0D 04 00 11 0A")),
        (0x14, bytes.fromhex("0D 14 00 21 0A")),
        (0x15, bytes.fromhex("0D 15 00 22 0A")),
        (0x19, bytes.fromhex("0D 19 00 26 0A")),
    ],
)
def test_build_query_matches_symcon_source(command: int, expected: bytes) -> None:
    """All generated requests must exactly match the supplied source."""

    assert protocol.build_query(command) == expected


def test_parse_and_decode_little_endian_value() -> None:
    """A two-byte response is validated and decoded little-endian."""

    frame = protocol.build_frame(0x08, bytes.fromhex("34 12"))
    payload = protocol.parse_frame(frame, 0x08)
    assert payload == bytes.fromhex("34 12")
    spec = next(
        item for item in protocol.QUERY_SPECS if item.key == "water_consumption_24h"
    )
    assert protocol.decode_value(payload, spec) == 0x1234


@pytest.mark.parametrize(
    ("frame_hex", "command", "expected"),
    [
        ("0D 25 02 D8 01 0D 0A", 0x25, 472),
        ("0D 02 02 5B 01 6D 0A", 0x02, 347),
        ("0D 11 02 01 00 21 0A", 0x11, 1),
        ("0D 10 04 08 02 00 00 2B 0A", 0x10, 520),
        ("0D 14 02 00 00 23 0A", 0x14, 0),
    ],
)
def test_published_device_captures(frame_hex: str, command: int, expected: int) -> None:
    """Real AQA Perla S captures pass checksum and endian decoding."""

    query_spec = next(item for item in protocol.QUERY_SPECS if item.command == command)
    payload = protocol.parse_frame(bytes.fromhex(frame_hex), command)
    assert protocol.decode_value(payload, query_spec) == expected


def test_decode_salt_scales_grams_to_kilograms() -> None:
    """The original script divides the four-byte salt counter by 1000."""

    spec = next(
        item for item in protocol.QUERY_SPECS if item.key == "total_salt_consumption"
    )
    assert protocol.decode_value((1250).to_bytes(4, "little"), spec) == 1.25


def test_decode_software_version_capture() -> None:
    """The SoftControl firmware response is decoded and control bytes removed."""

    spec = next(item for item in protocol.QUERY_SPECS if item.key == "software_version")
    payload = b"Version: 3.94#155"
    frame = protocol.build_frame(0x19, payload)
    assert frame == bytes.fromhex(
        "0D 19 11 56 65 72 73 69 6F 6E 3A 20 33 2E 39 34 23 31 35 35 03 0A"
    )
    assert protocol.decode_value(protocol.parse_frame(frame, 0x19), spec) == (
        "Version: 3.94#155"
    )


def test_rejects_invalid_ascii_response() -> None:
    """Text registers must not leak undecodable data into entity states."""

    spec = next(
        item for item in protocol.QUERY_SPECS if item.key == "commissioning_date"
    )
    with pytest.raises(protocol.BwtResponseError):
        protocol.decode_value(b"\xff", spec)


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [(0, 0), (1, 1), (41, 41), (0x82, 2), (0x87, 7), (0xA9, 41)],
)
def test_normalize_regeneration_step(raw_value: int, expected: int) -> None:
    """SoftControl 1.5 ignores bit 7 before looking up the step text."""

    assert protocol.normalize_regeneration_step(raw_value) == expected


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        ("Version: 3.94#155", ("3.94", "155")),
        ("3.94#155", ("3.94", "155")),
        ("Version: 3.94", ("3.94", None)),
    ],
)
def test_split_software_version(
    response: str, expected: tuple[str, str | None]
) -> None:
    """Firmware components are split as implemented by SoftControl."""

    assert protocol.split_software_version(response) == expected


def test_rejects_bad_checksum() -> None:
    """Corrupted frames must not update Home Assistant entities."""

    frame = bytearray(protocol.build_frame(0x04, b"\x03"))
    frame[-2] ^= 0x01
    with pytest.raises(protocol.BwtChecksumError):
        protocol.parse_frame(bytes(frame), 0x04)


def test_rejects_wrong_command() -> None:
    """A valid response for a different request is not accepted."""

    with pytest.raises(protocol.BwtResponseError):
        protocol.parse_frame(protocol.build_frame(0x03, b"\x01\x00"), 0x02)


def test_rejects_wrong_payload_length() -> None:
    """Known registers enforce the response width documented by the old code."""

    spec = next(
        item for item in protocol.QUERY_SPECS if item.key == "water_consumption_24h"
    )
    with pytest.raises(protocol.BwtResponseError):
        protocol.decode_value(b"\x01", spec)

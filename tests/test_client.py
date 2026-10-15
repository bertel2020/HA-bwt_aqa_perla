"""Tests for the asynchronous BWT AQA Perla client."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import pytest

PACKAGE = "bwt_client_pkg"
PACKAGE_PATH = Path(__file__).parents[1] / "custom_components" / "bwt_aqa_perla"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        f"{PACKAGE}.{name}", PACKAGE_PATH / f"{name}.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# Load protocol and client without importing the Home Assistant package.
sys.modules[PACKAGE] = types.ModuleType(PACKAGE)
sys.modules[PACKAGE].__path__ = [str(PACKAGE_PATH)]
protocol = _load("protocol")
client_module = _load("client")


class FakeWriter:
    """Writer that feeds scripted bytes into the paired reader."""

    def __init__(self, reader: asyncio.StreamReader, reply: bytes) -> None:
        self._reader = reader
        self._reply = reply
        self.written = b""
        self._closing = False

    def write(self, data: bytes) -> None:
        self.written += data
        self._reader.feed_data(self._reply)

    async def drain(self) -> None:
        return None

    def is_closing(self) -> bool:
        return self._closing

    def close(self) -> None:
        self._closing = True

    async def wait_closed(self) -> None:
        return None


def make_client(reply: bytes) -> client_module.BwtAqaPerlaClient:
    async def factory():
        reader = asyncio.StreamReader()
        return reader, FakeWriter(reader, reply)

    return client_module.BwtAqaPerlaClient(
        factory, response_timeout=0.2, command_delay=0
    )


SPEC = next(s for s in protocol.QUERY_SPECS if s.key == "water_consumption_24h")
QUERY = protocol.build_query(SPEC.command)
RESPONSE = protocol.build_frame(SPEC.command, (1234).to_bytes(2, "little"))


def test_query_decodes_response() -> None:
    asyncio.run(_test_query_decodes_response())


async def _test_query_decodes_response() -> None:
    assert await make_client(RESPONSE).async_query(SPEC) == 1234


def test_query_discards_noise_before_frame() -> None:
    asyncio.run(_test_query_discards_noise_before_frame())


async def _test_query_discards_noise_before_frame() -> None:
    assert await make_client(b"\x00\xff" + RESPONSE).async_query(SPEC) == 1234


def test_query_ignores_echoed_query() -> None:
    asyncio.run(_test_query_ignores_echoed_query())


async def _test_query_ignores_echoed_query() -> None:
    assert await make_client(QUERY + RESPONSE).async_query(SPEC) == 1234


def test_query_timeout_raises_connection_error() -> None:
    asyncio.run(_test_query_timeout_raises_connection_error())


async def _test_query_timeout_raises_connection_error() -> None:
    with pytest.raises(client_module.BwtConnectionError):
        await make_client(b"").async_query(SPEC)


def test_bad_checksum_raises_protocol_error() -> None:
    asyncio.run(_test_bad_checksum_raises_protocol_error())


async def _test_bad_checksum_raises_protocol_error() -> None:
    corrupt = RESPONSE[:-2] + bytes(((RESPONSE[-2] + 1) & 0xFF, RESPONSE[-1]))
    with pytest.raises(protocol.BwtProtocolError):
        await make_client(corrupt).async_query(SPEC)


def test_wrong_command_raises_protocol_error() -> None:
    asyncio.run(_test_wrong_command_raises_protocol_error())


async def _test_wrong_command_raises_protocol_error() -> None:
    other = protocol.build_frame(protocol.Command.REGENERATION_COUNT, b"\x01\x00")
    with pytest.raises(protocol.BwtProtocolError):
        await make_client(other).async_query(SPEC)

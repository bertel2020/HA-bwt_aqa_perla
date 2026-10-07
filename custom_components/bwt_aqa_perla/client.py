"""Asynchronous USB-serial and serial-over-TCP client."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from .protocol import (
    END_BYTE,
    QUERY_SPECS,
    START_BYTE,
    BwtProtocolError,
    QuerySpec,
    build_query,
    decode_value,
    parse_frame,
    split_software_version,
)

_LOGGER = logging.getLogger(__name__)

StreamFactory = Callable[
    [], Awaitable[tuple[asyncio.StreamReader, asyncio.StreamWriter]]
]


class BwtConnectionError(Exception):
    """Raised when communication with the device fails."""


class BwtAqaPerlaClient:
    """Client for one BWT AQA Perla connection."""

    def __init__(
        self,
        stream_factory: StreamFactory,
        *,
        response_timeout: float = 3.0,
        command_delay: float = 0.5,
    ) -> None:
        """Initialize the client."""

        self._stream_factory = stream_factory
        self._response_timeout = response_timeout
        self._command_delay = command_delay
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()

    @classmethod
    def for_tcp(cls, host: str, port: int, **kwargs: float) -> BwtAqaPerlaClient:
        """Create a client using a raw serial-over-TCP socket."""

        async def open_tcp() -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
            return await asyncio.open_connection(host, port)

        return cls(open_tcp, **kwargs)

    @classmethod
    def for_serial(
        cls, device: str, baudrate: int, **kwargs: float
    ) -> BwtAqaPerlaClient:
        """Create a client using a local serial device."""

        async def open_serial() -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
            from serial_asyncio_fast import open_serial_connection

            return await open_serial_connection(
                url=device,
                baudrate=baudrate,
                bytesize=8,
                parity="N",
                stopbits=1,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False,
            )

        return cls(open_serial, **kwargs)

    async def async_connect(self) -> None:
        """Open the connection if needed."""

        if self._writer is not None and not self._writer.is_closing():
            return
        try:
            async with asyncio.timeout(self._response_timeout):
                self._reader, self._writer = await self._stream_factory()
        except (TimeoutError, OSError, ValueError) as err:
            await self.async_close()
            raise BwtConnectionError(f"Unable to connect: {err}") from err

    async def async_close(self) -> None:
        """Close the active connection."""

        writer, self._writer, self._reader = self._writer, None, None
        if writer is None:
            return
        writer.close()
        try:
            await writer.wait_closed()
        except (OSError, RuntimeError):
            pass

    async def _async_read_frame(self) -> bytes:
        """Read exactly one length-framed response, resynchronizing on 0x0D."""

        assert self._reader is not None
        reader = self._reader

        while True:
            first = await reader.readexactly(1)
            if first[0] == START_BYTE:
                break
            _LOGGER.debug("Discarding byte 0x%02X before frame", first[0])

        header_tail = await reader.readexactly(2)
        payload_length = header_tail[1]
        remainder = await reader.readexactly(payload_length + 2)
        frame = bytes((START_BYTE,)) + header_tail + remainder
        if frame[-1] != END_BYTE:
            raise BwtProtocolError("Frame has no end marker")
        return frame

    async def async_query(self, spec: QuerySpec) -> int | float | str:
        """Query and decode one register."""

        async with self._lock:
            try:
                await self.async_connect()
                assert self._reader is not None and self._writer is not None
                query = build_query(spec.command)
                _LOGGER.debug("TX: %s", query.hex(" ").upper())
                self._writer.write(query)
                await self._writer.drain()
                async with asyncio.timeout(self._response_timeout):
                    frame = await self._async_read_frame()
                _LOGGER.debug("RX: %s", frame.hex(" ").upper())
                payload = parse_frame(frame, spec.command)
                return decode_value(payload, spec)
            except (
                TimeoutError,
                EOFError,
                asyncio.IncompleteReadError,
                OSError,
            ) as err:
                await self.async_close()
                raise BwtConnectionError(
                    f"Communication failed for command 0x{spec.command:02X}: {err}"
                ) from err
            except BwtProtocolError:
                # A corrupt or unexpected frame makes stream alignment uncertain.
                await self.async_close()
                raise

    async def async_update(self) -> dict[str, int | float | str]:
        """Read all known values sequentially."""

        values: dict[str, int | float | str] = {}
        for index, spec in enumerate(QUERY_SPECS):
            try:
                value = await self.async_query(spec)
                values[spec.key] = value
                if spec.key == "software_version" and isinstance(value, str):
                    electronics, control_panel = split_software_version(value)
                    values["software_version_power_electronics"] = electronics
                    if control_panel is not None:
                        values["software_version_control_panel"] = control_panel
            except (BwtConnectionError, BwtProtocolError):
                if not spec.optional:
                    raise
                _LOGGER.debug(
                    "Optional command 0x%02X is not supported by this device",
                    spec.command,
                    exc_info=True,
                )
            if index != len(QUERY_SPECS) - 1:
                await asyncio.sleep(self._command_delay)
        return values

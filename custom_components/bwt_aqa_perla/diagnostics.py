"""Diagnostics support for BWT AQA Perla."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from . import BwtAqaPerlaConfigEntry
from .const import CONF_SERIAL_PORT

TO_REDACT = {CONF_HOST, CONF_SERIAL_PORT}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: BwtAqaPerlaConfigEntry
) -> dict[str, Any]:
    """Return diagnostics: configuration, decoded values and raw frames."""

    runtime_data = entry.runtime_data
    coordinator = runtime_data.coordinator
    last_exception = coordinator.last_exception
    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "last_update_success": coordinator.last_update_success,
        "last_exception": repr(last_exception) if last_exception else None,
        "values": dict(coordinator.data or {}),
        "last_frames": {
            f"0x{command:02X}": frame
            for command, frame in sorted(runtime_data.client.last_frames.items())
        },
    }

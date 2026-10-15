"""BWT AQA Perla integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .client import BwtAqaPerlaClient
from .const import (
    CONF_BAUDRATE,
    CONF_CONNECTION_TYPE,
    CONF_FAST_POLL_INTERVAL,
    CONF_POLL_INTERVAL,
    CONF_SERIAL_PORT,
    CONF_TCP_PORT,
    CONNECTION_TCP,
    DEFAULT_BAUDRATE,
    DEFAULT_FAST_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    PLATFORMS,
    SOCKET_PREFIX,
)
from .coordinator import BwtAqaPerlaCoordinator


@dataclass(slots=True)
class BwtAqaPerlaRuntimeData:
    """Runtime objects for one config entry."""

    client: BwtAqaPerlaClient
    coordinator: BwtAqaPerlaCoordinator


type BwtAqaPerlaConfigEntry = ConfigEntry[BwtAqaPerlaRuntimeData]


def create_client(data: dict) -> BwtAqaPerlaClient:
    """Create a client from the connection stored in a config entry.

    A "socket://host:port" URL selects the raw TCP bridge, anything else is a
    local serial device.
    """

    port = data[CONF_SERIAL_PORT]
    if port.startswith(SOCKET_PREFIX):
        url = urlparse(port)
        return BwtAqaPerlaClient.for_tcp(url.hostname or "", url.port or 0)
    return BwtAqaPerlaClient.for_serial(
        port, int(data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE))
    )


def migrate_legacy_data(
    data: dict[str, Any], options: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Convert pre-1.1 entry data to the single-URL model.

    Returns the new data, new options and the unique ID. Polling intervals
    move to the options; the baud rate (serial only) moves into the data.
    """

    effective = {**data, **options}
    if data.get(CONF_CONNECTION_TYPE) == CONNECTION_TCP:
        port = f"{SOCKET_PREFIX}{data[CONF_HOST]}:{int(data[CONF_TCP_PORT])}"
        new_data: dict[str, Any] = {CONF_SERIAL_PORT: port}
    else:
        port = data[CONF_SERIAL_PORT]
        new_data = {
            CONF_SERIAL_PORT: port,
            CONF_BAUDRATE: int(effective.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)),
        }
    new_options = {
        key: int(effective[key])
        for key in (CONF_POLL_INTERVAL, CONF_FAST_POLL_INTERVAL)
        if key in effective
    }
    return new_data, new_options, port


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate entries to the single-URL data model (minor version 3)."""

    if entry.version == 1 and entry.minor_version < 3:
        data, options, unique_id = migrate_legacy_data(
            dict(entry.data), dict(entry.options)
        )
        hass.config_entries.async_update_entry(
            entry, data=data, options=options, unique_id=unique_id, minor_version=3
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: BwtAqaPerlaConfigEntry) -> bool:
    """Set up BWT AQA Perla from a config entry."""

    effective_config = {**entry.data, **entry.options}
    client = create_client(effective_config)
    coordinator = BwtAqaPerlaCoordinator(
        hass,
        entry,
        client,
        int(effective_config.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)),
        int(effective_config.get(CONF_FAST_POLL_INTERVAL, DEFAULT_FAST_POLL_INTERVAL)),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = BwtAqaPerlaRuntimeData(client, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: BwtAqaPerlaConfigEntry
) -> bool:
    """Unload a config entry and close its connection."""

    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.client.async_close()
    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Allow removing the device from the UI."""

    return True

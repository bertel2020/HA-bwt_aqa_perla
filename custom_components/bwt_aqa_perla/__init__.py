"""BWT AQA Perla integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .client import BwtAqaPerlaClient
from .const import (
    CONF_BAUDRATE,
    CONF_CONNECTION_TYPE,
    CONF_FAST_POLL_INTERVAL,
    CONF_POLL_INTERVAL,
    CONF_SERIAL_PORT,
    CONF_TCP_PORT,
    CONNECTION_SERIAL,
    CONNECTION_TCP,
    DEFAULT_FAST_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    PLATFORMS,
)
from .coordinator import BwtAqaPerlaCoordinator


@dataclass(slots=True)
class BwtAqaPerlaRuntimeData:
    """Runtime objects for one config entry."""

    client: BwtAqaPerlaClient
    coordinator: BwtAqaPerlaCoordinator


type BwtAqaPerlaConfigEntry = ConfigEntry[BwtAqaPerlaRuntimeData]


def create_client(data: dict) -> BwtAqaPerlaClient:
    """Create a client from config-entry data."""

    if data[CONF_CONNECTION_TYPE] == CONNECTION_SERIAL:
        return BwtAqaPerlaClient.for_serial(
            data[CONF_SERIAL_PORT], int(data[CONF_BAUDRATE])
        )
    return BwtAqaPerlaClient.for_tcp(data[CONF_HOST], int(data[CONF_TCP_PORT]))


async def async_setup_entry(hass: HomeAssistant, entry: BwtAqaPerlaConfigEntry) -> bool:
    """Set up BWT AQA Perla from a config entry."""

    effective_config = {**entry.data, **entry.options}
    client = create_client(effective_config)
    coordinator = BwtAqaPerlaCoordinator(
        hass,
        client,
        int(effective_config.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)),
        int(effective_config.get(CONF_FAST_POLL_INTERVAL, DEFAULT_FAST_POLL_INTERVAL)),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = BwtAqaPerlaRuntimeData(client, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Drop the ".0" that number selectors left in TCP unique IDs (1.1 -> 1.2).

    The stored port stays as is: 8899.0 equals 8899, and it is cast to int
    wherever it is used.
    """

    if entry.version == 1 and entry.minor_version < 2:
        unique_id = entry.unique_id
        if entry.data.get(CONF_CONNECTION_TYPE) == CONNECTION_TCP:
            unique_id = f"tcp:{entry.data[CONF_HOST]}:{int(entry.data[CONF_TCP_PORT])}"
        hass.config_entries.async_update_entry(
            entry, unique_id=unique_id, minor_version=2
        )
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: BwtAqaPerlaConfigEntry
) -> bool:
    """Unload a config entry and close its connection."""

    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.client.async_close()
    return True

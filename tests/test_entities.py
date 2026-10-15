"""Setup, entity and diagnostics tests."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.bwt_aqa_perla.const import DOMAIN
from custom_components.bwt_aqa_perla.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import FakeClient


def _entity_id(hass: HomeAssistant, entry: MockConfigEntry, platform: str, key: str):
    return er.async_get(hass).async_get_entity_id(
        platform, DOMAIN, f"{entry.entry_id}_{key}"
    )


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_use_reported_values(
    hass: HomeAssistant, client: FakeClient, tcp_entry: MockConfigEntry
) -> None:
    await _setup(hass, tcp_entry)

    water = hass.states.get(
        _entity_id(hass, tcp_entry, "sensor", "total_water_consumption")
    )
    assert water.state == "5000"
    device_type = hass.states.get(_entity_id(hass, tcp_entry, "sensor", "device_type"))
    assert device_type.state == "type_12"
    percent = hass.states.get(
        _entity_id(hass, tcp_entry, "sensor", "remaining_capacity_percent_column_1")
    )
    assert percent.state == "75.0"
    version = hass.states.get(
        _entity_id(hass, tcp_entry, "sensor", "software_version_power_electronics")
    )
    assert version.state == "3.94"


async def test_unreported_and_unused_values_get_no_entity(
    hass: HomeAssistant, client: FakeClient, tcp_entry: MockConfigEntry
) -> None:
    await _setup(hass, tcp_entry)

    # Optional command the device did not answer.
    assert _entity_id(hass, tcp_entry, "sensor", "peak_flow_today") is None
    # Column 2 has a nominal capacity of 0, so no percentage exists.
    assert (
        _entity_id(hass, tcp_entry, "sensor", "remaining_capacity_percent_column_2")
        is None
    )


async def test_regeneration_binary_sensor(
    hass: HomeAssistant, client: FakeClient, tcp_entry: MockConfigEntry
) -> None:
    client.values["regeneration_step"] = 0x82  # step 2 with flag bit 7 set
    await _setup(hass, tcp_entry)

    entity_id = _entity_id(hass, tcp_entry, "binary_sensor", "regeneration_active")
    assert hass.states.get(entity_id).state == "on"
    step = hass.states.get(_entity_id(hass, tcp_entry, "sensor", "regeneration_step"))
    assert step.state == "step_2"
    assert step.attributes["flag_bit_7"] is True


async def test_failed_poll_marks_entities_unavailable_then_recovers(
    hass: HomeAssistant, client: FakeClient, tcp_entry: MockConfigEntry
) -> None:
    await _setup(hass, tcp_entry)
    entity_id = _entity_id(hass, tcp_entry, "sensor", "total_water_consumption")

    client.fail = True
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=20))
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "unavailable"

    client.fail = False
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=40))
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "5000"


async def test_unload_closes_client(
    hass: HomeAssistant, client: FakeClient, tcp_entry: MockConfigEntry
) -> None:
    await _setup(hass, tcp_entry)
    closed = client.closed
    assert await hass.config_entries.async_unload(tcp_entry.entry_id)
    assert tcp_entry.state is ConfigEntryState.NOT_LOADED
    assert client.closed > closed


async def test_diagnostics_redacts_target(
    hass: HomeAssistant, client: FakeClient, tcp_entry: MockConfigEntry
) -> None:
    await _setup(hass, tcp_entry)
    result = await async_get_config_entry_diagnostics(hass, tcp_entry)

    assert result["entry"]["data"]["serial_port"] == "**REDACTED**"
    assert result["last_update_success"] is True
    assert result["values"]["total_water_consumption"] == 5000
    assert result["last_frames"] == {"0x08": "0D 08 02 78 00 8F 0A"}


async def test_slow_values_are_polled_less_often_than_fast_values(
    hass: HomeAssistant, client: FakeClient, tcp_entry: MockConfigEntry
) -> None:
    now = [1000.0]
    with patch(
        "custom_components.bwt_aqa_perla.coordinator.time.monotonic",
        side_effect=lambda: now[0],
    ):
        await _setup(hass, tcp_entry)
        assert "total_water_consumption" in client.calls[0]
        assert "regeneration_step" in client.calls[0]

        # Next fast cycle: only the regeneration step is read.
        now[0] += 15
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=16))
        await hass.async_block_till_done()
        assert client.calls[-1] == ["regeneration_step"]

        # Once the slow interval has elapsed, everything is read again.
        now[0] += 50
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=32))
        await hass.async_block_till_done()
        assert "total_water_consumption" in client.calls[-1]
        assert "regeneration_step" in client.calls[-1]

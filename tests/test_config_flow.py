"""Config, options and reconfigure flow tests."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bwt_aqa_perla.const import DOMAIN

from .conftest import FakeClient


async def _start_tcp(hass: HomeAssistant, host: str = "192.0.2.10") -> dict:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"connection_type": "tcp"}
    )
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host, "tcp_port": 8899}
    )


async def test_tcp_flow_creates_entry(hass: HomeAssistant, client: FakeClient) -> None:
    result = await _start_tcp(hass)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "BWT AQA Perla (192.0.2.10)"
    assert result["data"]["host"] == "192.0.2.10"
    assert result["result"].unique_id == "tcp:192.0.2.10:8899"


async def test_tcp_flow_cannot_connect_then_recovers(
    hass: HomeAssistant, client: FakeClient
) -> None:
    client.fail = True
    result = await _start_tcp(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    client.fail = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": "192.0.2.10", "tcp_port": 8899}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_duplicate_tcp_entry_aborts(
    hass: HomeAssistant, client: FakeClient, tcp_entry: MockConfigEntry
) -> None:
    tcp_entry.add_to_hass(hass)
    result = await _start_tcp(hass)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_serial_flow_offers_detected_ports(
    hass: HomeAssistant, client: FakeClient
) -> None:
    ports = [{"value": "/dev/serial/by-id/usb-test", "label": "usb-test"}]
    with patch(
        "custom_components.bwt_aqa_perla.config_flow._list_serial_ports",
        return_value=ports,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"connection_type": "serial"}
        )
        assert result["step_id"] == "serial"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"serial_port": "/dev/serial/by-id/usb-test", "baudrate": "9600"},
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == "serial:/dev/serial/by-id/usb-test"


async def test_reconfigure_updates_host_and_unique_id(
    hass: HomeAssistant, client: FakeClient, tcp_entry: MockConfigEntry
) -> None:
    tcp_entry.add_to_hass(hass)
    result = await tcp_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": "192.0.2.20", "tcp_port": 8899}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert tcp_entry.data["host"] == "192.0.2.20"
    assert tcp_entry.unique_id == "tcp:192.0.2.20:8899"
    assert tcp_entry.title == "BWT AQA Perla (192.0.2.20)"


async def test_options_flow_saves_intervals(
    hass: HomeAssistant, client: FakeClient, tcp_entry: MockConfigEntry
) -> None:
    tcp_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(tcp_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"poll_interval": 120, "fast_poll_interval": 10}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert tcp_entry.options == {"poll_interval": 120, "fast_poll_interval": 10}


async def test_migration_normalizes_float_port(
    hass: HomeAssistant, client: FakeClient
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="BWT AQA Perla (192.0.2.10)",
        unique_id="tcp:192.0.2.10:8899.0",
        minor_version=1,
        data={"connection_type": "tcp", "host": "192.0.2.10", "tcp_port": 8899.0},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.unique_id == "tcp:192.0.2.10:8899"
    assert entry.minor_version == 2

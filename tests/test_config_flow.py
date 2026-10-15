"""Config, options, reconfigure flow and migration tests."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bwt_aqa_perla import migrate_legacy_data
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
    assert result["data"] == {"serial_port": "socket://192.0.2.10:8899"}
    assert result["result"].unique_id == "socket://192.0.2.10:8899"


async def test_tcp_flow_rejects_invalid_host(
    hass: HomeAssistant, client: FakeClient
) -> None:
    result = await _start_tcp(hass, host="bad/host")
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_host"}


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


async def test_serial_flow_stores_port_and_baudrate(
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
            {"serial_port": "/dev/serial/by-id/usb-test", "baudrate": "19200"},
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "serial_port": "/dev/serial/by-id/usb-test",
        "baudrate": 19200,
    }
    assert result["result"].unique_id == "/dev/serial/by-id/usb-test"


async def test_reconfigure_tcp_updates_host_unique_id_and_title(
    hass: HomeAssistant, client: FakeClient, tcp_entry: MockConfigEntry
) -> None:
    tcp_entry.add_to_hass(hass)
    result = await tcp_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "tcp"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": "192.0.2.20", "tcp_port": 8899}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert tcp_entry.data == {"serial_port": "socket://192.0.2.20:8899"}
    assert tcp_entry.unique_id == "socket://192.0.2.20:8899"
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


def test_migrate_legacy_tcp_data() -> None:
    data, options, unique_id = migrate_legacy_data(
        {
            "connection_type": "tcp",
            "host": "192.0.2.10",
            "tcp_port": 8899.0,
            "poll_interval": 90.0,
            "fast_poll_interval": 10.0,
        },
        {},
    )
    assert data == {"serial_port": "socket://192.0.2.10:8899"}
    assert options == {"poll_interval": 90, "fast_poll_interval": 10}
    assert unique_id == "socket://192.0.2.10:8899"


def test_migrate_legacy_serial_moves_baudrate_into_data() -> None:
    data, options, unique_id = migrate_legacy_data(
        {
            "connection_type": "serial",
            "serial_port": "/dev/ttyUSB0",
            "baudrate": "9600",
            "poll_interval": 60,
        },
        {"baudrate": "19200", "poll_interval": 120},
    )
    assert data == {"serial_port": "/dev/ttyUSB0", "baudrate": 19200}
    assert options == {"poll_interval": 120}
    assert unique_id == "/dev/ttyUSB0"


async def test_setup_migrates_legacy_entry(
    hass: HomeAssistant, client: FakeClient
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="BWT AQA Perla (192.0.2.10)",
        unique_id="tcp:192.0.2.10:8899.0",
        minor_version=2,
        data={
            "connection_type": "tcp",
            "host": "192.0.2.10",
            "tcp_port": 8899.0,
            "poll_interval": 60.0,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.data == {"serial_port": "socket://192.0.2.10:8899"}
    assert entry.options == {"poll_interval": 60}
    assert entry.unique_id == "socket://192.0.2.10:8899"
    assert entry.minor_version == 3

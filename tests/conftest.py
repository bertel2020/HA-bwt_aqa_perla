"""Fixtures for Home Assistant integration tests."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bwt_aqa_perla.client import BwtConnectionError
from custom_components.bwt_aqa_perla.const import (
    CONF_CONNECTION_TYPE,
    CONF_TCP_PORT,
    CONNECTION_TCP,
    DOMAIN,
)

VALUES = {
    "device_type": 12,
    "water_consumption_24h": 120,
    "total_water_consumption": 5000,
    "total_salt_consumption": 12.5,
    "nominal_capacity_column_1": 800,
    "nominal_capacity_column_2": 0,
    "remaining_capacity_column_1": 600,
    "remaining_capacity_column_2": 0,
    "regeneration_count": 3,
    "regeneration_step": 0,
    "software_version": "Version:3.94#155",
}


class FakeClient:
    """Stand-in for BwtAqaPerlaClient serving canned values."""

    def __init__(self) -> None:
        self.values = dict(VALUES)
        self.fail = False
        self.last_frames = {0x08: "0D 08 02 78 00 8F 0A"}
        self.closed = 0

    async def async_query(self, spec):
        if self.fail:
            raise BwtConnectionError("boom")
        return self.values[spec.key]

    async def async_read(self, specs):
        if self.fail:
            raise BwtConnectionError("boom")
        return {s.key: self.values[s.key] for s in specs if s.key in self.values}

    async def async_close(self) -> None:
        self.closed += 1


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load the custom integration under test."""


@pytest.fixture
def client() -> Iterator[FakeClient]:
    """Patch client creation with a fake client."""

    fake = FakeClient()
    with (
        patch("custom_components.bwt_aqa_perla.create_client", return_value=fake),
        patch(
            "custom_components.bwt_aqa_perla.config_flow.create_client",
            return_value=fake,
        ),
    ):
        yield fake


@pytest.fixture
def tcp_entry() -> MockConfigEntry:
    """Return a TCP config entry."""

    return MockConfigEntry(
        domain=DOMAIN,
        title="BWT AQA Perla (192.0.2.10)",
        unique_id="tcp:192.0.2.10:8899",
        data={
            CONF_CONNECTION_TYPE: CONNECTION_TCP,
            "host": "192.0.2.10",
            CONF_TCP_PORT: 8899,
        },
    )

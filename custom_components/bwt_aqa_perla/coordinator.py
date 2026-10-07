"""Data coordinator for BWT AQA Perla."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import BwtAqaPerlaClient, BwtConnectionError
from .const import DOMAIN
from .protocol import BwtProtocolError

_LOGGER = logging.getLogger(__name__)


class BwtAqaPerlaCoordinator(DataUpdateCoordinator[dict[str, int | float | str]]):
    """Coordinate sequential polling of the serial bus."""

    def __init__(
        self, hass: HomeAssistant, client: BwtAqaPerlaClient, poll_interval: int
    ) -> None:
        """Initialize the coordinator."""

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, int | float | str]:
        """Fetch all values from the appliance."""

        try:
            return await self.client.async_update()
        except (BwtConnectionError, BwtProtocolError) as err:
            raise UpdateFailed(str(err)) from err
        finally:
            # A fresh connection for every poll avoids stale USB and bridge
            # sessions, a known failure mode of this appliance generation.
            await self.client.async_close()

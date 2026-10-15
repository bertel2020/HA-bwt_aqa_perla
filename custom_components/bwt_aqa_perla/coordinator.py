"""Data coordinator for BWT AQA Perla."""

from __future__ import annotations

import logging
import time
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import BwtAqaPerlaClient, BwtConnectionError
from .const import DOMAIN
from .protocol import FAST_SPECS, SLOW_SPECS, BwtProtocolError
from .tracker import ValueTracker

_LOGGER = logging.getLogger(__name__)


class BwtAqaPerlaCoordinator(DataUpdateCoordinator[dict[str, int | float | str]]):
    """Coordinate sequential polling of the serial bus."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: BwtAqaPerlaClient,
        poll_interval: int,
        fast_poll_interval: int,
    ) -> None:
        """Initialize the coordinator."""

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=min(poll_interval, fast_poll_interval)),
        )
        self.client = client
        self._tracker = ValueTracker()
        self._poll_interval = poll_interval
        self._last_slow_poll: float | None = None

    async def _async_update_data(self) -> dict[str, int | float | str]:
        """Fetch all values from the appliance."""

        try:
            now = time.monotonic()
            # Fast values (regeneration step) are read on every cycle; the
            # remaining values only when the slower interval has elapsed.
            slow_due = (
                self._last_slow_poll is None
                or now - self._last_slow_poll >= self._poll_interval - 1
            )
            specs = FAST_SPECS + SLOW_SPECS if slow_due else FAST_SPECS
            received = await self.client.async_read(specs)
            if slow_due:
                self._last_slow_poll = now
            return self._tracker.update((spec.key for spec in specs), received)
        except (BwtConnectionError, BwtProtocolError) as err:
            raise UpdateFailed(str(err)) from err
        finally:
            # A fresh connection for every poll avoids stale USB and bridge
            # sessions, a known failure mode of this appliance generation.
            await self.client.async_close()

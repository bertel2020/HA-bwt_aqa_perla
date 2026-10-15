"""Data coordinator for BWT AQA Perla."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .client import BwtAqaPerlaClient, BwtConnectionError
from .const import CONF_SERIAL_PORT, DOMAIN, NO_DATA_ISSUE_AFTER
from .protocol import FAST_SPECS, SLOW_SPECS, BwtProtocolError
from .tracker import ValueTracker

_LOGGER = logging.getLogger(__name__)


class BwtAqaPerlaCoordinator(DataUpdateCoordinator[dict[str, int | float | str]]):
    """Coordinate sequential polling of the serial bus."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: BwtAqaPerlaClient,
        poll_interval: int,
        fast_poll_interval: int,
    ) -> None:
        """Initialize the coordinator."""

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=min(poll_interval, fast_poll_interval)),
        )
        self.client = client
        self._tracker = ValueTracker()
        self._poll_interval = poll_interval
        self._last_slow_poll: float | None = None
        self._last_success_monotonic = time.monotonic()
        self.last_success: datetime | None = None
        self.failed_polls = 0

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
            values = self._tracker.update((spec.key for spec in specs), received)
        except (BwtConnectionError, BwtProtocolError) as err:
            self.failed_polls += 1
            self._update_no_data_issue(failed=True)
            raise UpdateFailed(str(err)) from err
        finally:
            # A fresh connection for every poll avoids stale USB and bridge
            # sessions, a known failure mode of this appliance generation.
            await self.client.async_close()
        self.last_success = dt_util.utcnow()
        self._last_success_monotonic = time.monotonic()
        self._update_no_data_issue(failed=False)
        return values

    def _update_no_data_issue(self, *, failed: bool) -> None:
        """Raise a repair issue after a long outage and clear it on recovery."""

        issue_id = f"no_data_{self.config_entry.entry_id}"
        if not failed:
            ir.async_delete_issue(self.hass, DOMAIN, issue_id)
        elif time.monotonic() - self._last_success_monotonic > NO_DATA_ISSUE_AFTER:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key="no_data",
                translation_placeholders={
                    "port": self.config_entry.data[CONF_SERIAL_PORT]
                },
            )

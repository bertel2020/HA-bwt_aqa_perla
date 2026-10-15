"""Binary sensor platform for BWT AQA Perla."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BwtAqaPerlaConfigEntry
from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import BwtAqaPerlaCoordinator
from .protocol import normalize_regeneration_step

PARALLEL_UPDATES = 0

REGENERATION_ACTIVE = BinarySensorEntityDescription(
    key="regeneration_active",
    translation_key="regeneration_active",
    device_class=BinarySensorDeviceClass.RUNNING,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BwtAqaPerlaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensors from a config entry."""

    async_add_entities(
        [BwtAqaPerlaRegenerationActive(entry.runtime_data.coordinator, entry)]
    )


class BwtAqaPerlaRegenerationActive(
    CoordinatorEntity[BwtAqaPerlaCoordinator], BinarySensorEntity
):
    """On while the appliance is not in normal operation."""

    _attr_has_entity_name = True
    entity_description = REGENERATION_ACTIVE

    def __init__(
        self, coordinator: BwtAqaPerlaCoordinator, entry: BwtAqaPerlaConfigEntry
    ) -> None:
        """Initialize the binary sensor."""

        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{REGENERATION_ACTIVE.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=entry.title,
        )

    @property
    def available(self) -> bool:
        """Return whether the regeneration step was reported."""

        return super().available and "regeneration_step" in self.coordinator.data

    @property
    def is_on(self) -> bool | None:
        """Return whether a regeneration step other than operation is active."""

        value = self.coordinator.data.get("regeneration_step")
        if not isinstance(value, int):
            return None
        return normalize_regeneration_step(value) != 0

"""Sensor platform for BWT AQA Perla."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfMass, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BwtAqaPerlaConfigEntry
from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import BwtAqaPerlaCoordinator
from .protocol import normalize_regeneration_step

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="device_type",
        translation_key="device_type",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="peak_flow_today",
        translation_key="peak_flow_today",
        native_unit_of_measurement="L/h",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="peak_flow_24h",
        translation_key="peak_flow_24h",
        native_unit_of_measurement="L/h",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="peak_flow_since_commissioning",
        translation_key="peak_flow_since_commissioning",
        native_unit_of_measurement="L/h",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="water_consumption_24h",
        translation_key="water_consumption_24h",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key="total_water_consumption",
        translation_key="total_water_consumption",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="total_salt_consumption",
        translation_key="total_salt_consumption",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=3,
    ),
    SensorEntityDescription(
        key="nominal_capacity_column_1",
        translation_key="nominal_capacity_column_1",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="nominal_capacity_column_2",
        translation_key="nominal_capacity_column_2",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="remaining_capacity_column_1",
        translation_key="remaining_capacity_column_1",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="remaining_capacity_column_2",
        translation_key="remaining_capacity_column_2",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="regeneration_count",
        translation_key="regeneration_count",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="regeneration_count_since_service",
        translation_key="regeneration_count_since_service",
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key="regeneration_step",
        translation_key="regeneration_step",
    ),
    SensorEntityDescription(
        key="regenerant_saving",
        translation_key="regenerant_saving",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="commissioning_date",
        translation_key="commissioning_date",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="software_version",
        translation_key="software_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="software_version_power_electronics",
        translation_key="software_version_power_electronics",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="software_version_control_panel",
        translation_key="software_version_control_panel",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

DEVICE_TYPES = {
    0: "Kein Typ",
    1: "Rondomat Duo 1",
    2: "Rondomat Duo 2",
    3: "Rondomat Duo 3",
    4: "Rondomat Duo 6",
    5: "Rondomat Duo 10",
    6: "Rondomat Duo S1TW",
    7: "Rondomat Duo S2TW",
    8: "Rondomat Duo S3TW",
    9: "Rondomat Duo 1 I",
    10: "Rondomat Duo 2 I",
    11: "Rondomat Duo 3 I",
    12: "Aqua Perla",
    13: "Aqua Life",
    14: "Mephisto",
    15: "Special",
}
REGENERATION_STEPS = {
    0: "Säulen in Betrieb",
    1: "Rückspülen",
    2: "Besalzen",
    3: "Keimschutz",
    4: "Verdrängen",
    5: "Nachspeisung 1 Solebehälter",
    6: "Spülen",
    7: "T7",
    8: "Säulenwechsel-Start",
    9: "Säulenwechsel",
    10: "Nachspeisung 2 Solebehälter",
    11: "T-Spülen",
    12: "T-Spülen-1",
    13: "T-Spülen-2",
    14: "T-Spülen-3",
    15: "T-Säulenwechsel-Start",
    16: "T-Säulenwechsel-Pos",
    17: "T-Power On",
    18: "T-Power On-1",
    19: "T-Power On-2",
    20: "T-Power On-3",
    21: "T-Power On-4",
    22: "T-Power On-5",
    23: "T-Power On-6",
    24: "T-Power On >8h",
    25: "T-Power On >8h-1",
    26: "T-Neupositionierung",
    27: "T-Neupositionierung-1",
    28: "T-Power On break",
    29: "T-Power On wait",
    30: "T-Hygiene-0",
    31: "T-Hygiene-1",
    32: "T-Hygiene-2",
    33: "T-Hygiene-3",
    34: "T-Hygiene-4",
    35: "T-Start_PowOff-1",
    36: "T-Start_PowOff-2",
    37: "T-DVGW-1",
    38: "T-DVGW-2",
    39: "T-Soleventil-0",
    40: "T-Soleventil-1",
    41: "T-Soleventil-2",
}
REGENERATION_SHORT_CODES = {
    0: "Normalbetrieb",
    **{value: f"T{value}" for value in range(1, 8)},
    8: "T8-Start",
    9: "T8",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BwtAqaPerlaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""

    async_add_entities(
        BwtAqaPerlaSensor(entry.runtime_data.coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class BwtAqaPerlaSensor(CoordinatorEntity[BwtAqaPerlaCoordinator], SensorEntity):
    """Representation of one BWT value."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BwtAqaPerlaCoordinator,
        entry: BwtAqaPerlaConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""

        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=MODEL,
        )

    @property
    def available(self) -> bool:
        """Return whether this value was included in the last update."""

        return (
            super().available and self.entity_description.key in self.coordinator.data
        )

    @property
    def native_value(self) -> int | float | str | None:
        """Return the latest decoded value."""

        value = self.coordinator.data.get(self.entity_description.key)
        if self.entity_description.key == "device_type" and isinstance(value, int):
            return DEVICE_TYPES.get(value, f"Typ {value}")
        if self.entity_description.key == "software_version" and isinstance(value, str):
            return value.removeprefix("Version:").strip()
        if self.entity_description.key == "regeneration_step" and isinstance(
            value, int
        ):
            normalized = normalize_regeneration_step(value)
            return REGENERATION_STEPS.get(normalized, f"Unbekannt ({normalized})")
        return value

    @property
    def extra_state_attributes(self) -> dict[str, int | bool | str] | None:
        """Expose the unmodified regeneration byte for diagnostics."""

        if self.entity_description.key != "regeneration_step":
            return None
        value = self.coordinator.data.get(self.entity_description.key)
        if not isinstance(value, int):
            return None
        normalized = normalize_regeneration_step(value)
        attributes: dict[str, int | bool | str] = {
            "raw_value": value,
            "normalized_step": normalized,
            "flag_bit_7": bool(value & 0x80),
        }
        if short_code := REGENERATION_SHORT_CODES.get(normalized):
            attributes["short_code"] = short_code
        return attributes

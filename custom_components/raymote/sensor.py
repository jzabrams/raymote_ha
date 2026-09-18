"""Telemetry sensors. Pin meanings and confidence levels: see PINMAP.md."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PIN_STATUS_TEXT
from .coordinator import RaymoteCoordinator
from .entity import RaymoteEntity


@dataclass(frozen=True, kw_only=True)
class RaymoteSensorDescription(SensorEntityDescription):
    pin: str


def _temp(key: str, name: str, pin: str, diagnostic: bool = False) -> RaymoteSensorDescription:
    return RaymoteSensorDescription(
        key=key,
        name=name,
        pin=pin,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC if diagnostic else None,
    )


SENSORS: tuple[RaymoteSensorDescription, ...] = (
    _temp("water_temp", "Water temperature", "v51"),
    _temp("water_in", "Water inlet temperature", "v3", diagnostic=True),
    _temp("water_out", "Water outlet temperature", "v4", diagnostic=True),
    _temp("ambient", "Ambient temperature", "v9"),
    _temp("coil", "Coil temperature", "v6", diagnostic=True),
    _temp("discharge", "Discharge temperature", "v5", diagnostic=True),
    RaymoteSensorDescription(
        key="status",
        name="Status",
        pin=PIN_STATUS_TEXT,
    ),
    RaymoteSensorDescription(
        key="compressor_starts",
        name="Compressor starts",
        pin="v25",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RaymoteSensorDescription(
        key="rssi",
        name="Wi-Fi signal",
        pin="v64",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(RaymoteSensor(coordinator, d) for d in SENSORS)


class RaymoteSensor(RaymoteEntity, SensorEntity):
    entity_description: RaymoteSensorDescription

    def __init__(self, coordinator: RaymoteCoordinator, description: RaymoteSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        value = self.coordinator.data.get(self.entity_description.pin)
        if isinstance(value, str):
            value = value.strip() or None
        return value

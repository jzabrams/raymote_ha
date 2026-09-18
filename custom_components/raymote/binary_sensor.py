"""Binary sensors: cloud connectivity and compressor running."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PIN_STATE, STATE_HEATING
from .entity import RaymoteEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RaymoteOnline(coordinator, "online"), RaymoteHeating(coordinator, "heating")])


class RaymoteOnline(RaymoteEntity, BinarySensorEntity):
    _attr_name = "Connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("online"))


class RaymoteHeating(RaymoteEntity, BinarySensorEntity):
    _attr_name = "Heating"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get(PIN_STATE) == STATE_HEATING

"""Shared base entity."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RaymoteCoordinator


class RaymoteEntity(CoordinatorEntity[RaymoteCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: RaymoteCoordinator, key: str) -> None:
        super().__init__(coordinator)
        # unique_id of the config entry is a hash of the token, never the token itself
        device_id = coordinator.config_entry.unique_id
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name="Pool Heat Pump",
            manufacturer="Raypak",
            model="Crosswind V",
        )

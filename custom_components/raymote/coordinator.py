"""Polling coordinator for Raymote."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RaymoteAuthError, RaymoteClient, RaymoteError
from .const import DOMAIN, SCAN_INTERVAL_SECONDS, WRITE_ACK_DELAY_SECONDS

_LOGGER = logging.getLogger(__name__)


class RaymoteCoordinator(DataUpdateCoordinator[dict]):
    """Holds the latest getAll pin dict, plus an "online" key."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: RaymoteClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        try:
            online = await self.client.is_connected()
            pins = await self.client.get_all()
        except RaymoteAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except RaymoteError as err:
            raise UpdateFailed(str(err)) from err
        return {**pins, "online": online}

    async def async_refresh_after_write(self) -> None:
        """The heater takes ~3s to acknowledge a write; refresh once it has."""
        await asyncio.sleep(WRITE_ACK_DELAY_SECONDS)
        await self.async_request_refresh()

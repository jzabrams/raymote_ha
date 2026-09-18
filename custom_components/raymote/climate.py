"""Climate entity: off/heat, pool/spa presets, setpoint."""
from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MODE_OFF,
    MODE_SPA,
    PIN_MODE,
    PIN_MODE_ACK,
    PIN_SETPOINT,
    PIN_SETPOINT_MAX,
    PIN_SETPOINT_MIN,
    PIN_STATE,
    PIN_WATER_TEMP,
    PRESETS,
    STATE_HEATING,
)
from .coordinator import RaymoteCoordinator
from .entity import RaymoteEntity

PRESET_TO_MODE = {v: k for k, v in PRESETS.items()}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([RaymoteClimate(hass.data[DOMAIN][entry.entry_id])])


class RaymoteClimate(RaymoteEntity, ClimateEntity):
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_target_temperature_step = 1
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_preset_modes = list(PRESETS.values())
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, coordinator: RaymoteCoordinator) -> None:
        super().__init__(coordinator, "climate")
        # remembered so HEAT after OFF returns to the mode the heater was in
        self._last_on_mode = MODE_SPA
        self._remember_mode()

    def _remember_mode(self) -> None:
        if self._mode in PRESETS:
            self._last_on_mode = self._mode

    @callback
    def _handle_coordinator_update(self) -> None:
        self._remember_mode()
        super()._handle_coordinator_update()

    @property
    def _pins(self) -> dict:
        return self.coordinator.data

    @property
    def _mode(self) -> int | None:
        return self._pins.get(PIN_MODE_ACK, self._pins.get(PIN_MODE))

    @property
    def available(self) -> bool:
        return super().available and bool(self._pins.get("online"))

    @property
    def hvac_mode(self) -> HVACMode | None:
        mode = self._mode
        if mode is None:
            return None
        return HVACMode.OFF if mode == MODE_OFF else HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction | None:
        # Taken from the heater's own state code: it keeps running ~1 min after
        # demand ends, so setpoint vs water temp is not a reliable indicator.
        if self._mode == MODE_OFF:
            return HVACAction.OFF
        if self._pins.get(PIN_STATE) == STATE_HEATING:
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def preset_mode(self) -> str | None:
        return PRESETS.get(self._mode)

    @property
    def current_temperature(self) -> float | None:
        return self._pins.get(PIN_WATER_TEMP)

    @property
    def target_temperature(self) -> float | None:
        return self._pins.get(PIN_SETPOINT)

    @property
    def min_temp(self) -> float:
        return self._pins.get(PIN_SETPOINT_MIN, 50)

    @property
    def max_temp(self) -> float:
        return self._pins.get(PIN_SETPOINT_MAX, 104)

    async def _write_mode(self, mode: int) -> None:
        if mode in PRESETS:
            self._last_on_mode = mode
        await self.coordinator.client.set_mode(mode)
        await self.coordinator.async_refresh_after_write()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self._write_mode(MODE_OFF)
        elif hvac_mode == HVACMode.HEAT:
            if self._mode in PRESETS:
                return
            await self._write_mode(self._last_on_mode)
        else:
            raise ServiceValidationError(f"Unsupported HVAC mode: {hvac_mode}")

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode not in PRESET_TO_MODE:
            raise ServiceValidationError(f"Unknown preset: {preset_mode}")
        await self._write_mode(PRESET_TO_MODE[preset_mode])

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        temp = int(round(temp))
        # the heater's own limits for the active mode (pool 44-95, spa 50-104)
        if not self.min_temp <= temp <= self.max_temp:
            raise ServiceValidationError(
                f"Setpoint {temp}°F is outside {self.min_temp}-{self.max_temp}°F for the current mode"
            )
        await self.coordinator.client.set_setpoint(temp)
        await self.coordinator.async_refresh_after_write()

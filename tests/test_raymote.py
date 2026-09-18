"""End-to-end test inside a real HA instance; the cloud client is mocked."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

from custom_components.raymote.api import RaymoteAuthError
from custom_components.raymote.const import DOMAIN

# trimmed from a real getAll snapshot (spa mode, idle)
PINS = {"v3": 96.1, "v4": 95.9, "v5": 96.8, "v6": 58.2, "v9": 79.2, "v25": 19, "v43": 92.0,
        "v51": 96.0, "v54": 2, "v55": "No Demand", "v64": -49.0, "v65": 1, "v67": 2,
        "v111": 92, "v235": 50, "v240": 104}
CLIENT = "custom_components.raymote.api.RaymoteClient"
CLIMATE = "climate.pool_heat_pump"


@pytest.fixture
def pins():
    return dict(PINS)


@pytest.fixture
def client(pins):
    with patch(f"{CLIENT}.get_all", AsyncMock(side_effect=lambda: dict(pins))), \
         patch(f"{CLIENT}.is_connected", AsyncMock(return_value=True)), \
         patch(f"{CLIENT}.set_mode", AsyncMock()) as set_mode, \
         patch(f"{CLIENT}.set_setpoint", AsyncMock()) as set_setpoint, \
         patch("custom_components.raymote.coordinator.WRITE_ACK_DELAY_SECONDS", 0):
        yield {"set_mode": set_mode, "set_setpoint": set_setpoint}


async def _setup(hass: HomeAssistant):
    hass.config.units = US_CUSTOMARY_SYSTEM
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"token": "tok"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    return result


async def test_flow_and_entities(hass, client):
    result = await _setup(hass)
    entry = result["result"]
    assert "tok" not in entry.unique_id

    state = hass.states.get(CLIMATE)
    assert state.state == "heat"
    assert state.attributes["hvac_action"] == "idle"
    assert state.attributes["preset_mode"] == "spa"
    assert state.attributes["temperature"] == 92
    assert state.attributes["current_temperature"] == 96
    assert state.attributes["min_temp"] == 50 and state.attributes["max_temp"] == 104
    assert hass.states.get("sensor.pool_heat_pump_status").state == "No Demand"
    assert hass.states.get("sensor.pool_heat_pump_water_temperature").state == "96.0"
    assert hass.states.get("binary_sensor.pool_heat_pump_heating").state == "off"


async def test_invalid_token(hass):
    with patch(f"{CLIENT}.get_all", AsyncMock(side_effect=RaymoteAuthError("Invalid token."))):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"token": "bad"})
    assert result["errors"] == {"base": "invalid_auth"}


async def test_writes(hass, client, pins):
    await _setup(hass)
    call = hass.services.async_call

    await call("climate", "set_temperature", {"entity_id": CLIMATE, "temperature": 90}, blocking=True)
    client["set_setpoint"].assert_awaited_once_with(90)

    with pytest.raises(Exception):
        await call("climate", "set_temperature", {"entity_id": CLIMATE, "temperature": 110}, blocking=True)
    client["set_setpoint"].assert_awaited_once()

    await call("climate", "set_preset_mode", {"entity_id": CLIMATE, "preset_mode": "pool"}, blocking=True)
    client["set_mode"].assert_awaited_with(1)

    pins.update({"v54": 1, "v67": 1})
    await call("climate", "set_hvac_mode", {"entity_id": CLIMATE, "hvac_mode": "off"}, blocking=True)
    client["set_mode"].assert_awaited_with(0)

    # HEAT after OFF returns to the last preset (pool), not the default
    pins.update({"v54": 0, "v67": 0})
    await next(iter(hass.data[DOMAIN].values())).async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(CLIMATE).state == "off"
    await call("climate", "set_hvac_mode", {"entity_id": CLIMATE, "hvac_mode": "heat"}, blocking=True)
    client["set_mode"].assert_awaited_with(1)


async def test_heating_action(hass, client, pins):
    pins.update({"v65": 6, "v55": "Heating"})
    await _setup(hass)
    assert hass.states.get(CLIMATE).attributes["hvac_action"] == "heating"
    assert hass.states.get("binary_sensor.pool_heat_pump_heating").state == "on"

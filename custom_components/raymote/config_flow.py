"""Config flow: device auth token (+ optional host)."""
from __future__ import annotations

import hashlib
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RaymoteAuthError, RaymoteClient, RaymoteError
from .const import CONF_HOST, CONF_TOKEN, DEFAULT_HOST, DOMAIN

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TOKEN): str,
        vol.Optional(CONF_HOST, default=DEFAULT_HOST): str,
    }
)


class RaymoteConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()
            host = user_input[CONF_HOST].strip().rstrip("/")
            client = RaymoteClient(async_get_clientsession(self.hass), token, host)
            try:
                await client.get_all()
            except RaymoteAuthError:
                errors["base"] = "invalid_auth"
            except RaymoteError:
                errors["base"] = "cannot_connect"
            else:
                # hash, so the token never appears in registries or diagnostics
                await self.async_set_unique_id(hashlib.sha256(token.encode()).hexdigest()[:16])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Raypak heat pump", data={CONF_TOKEN: token, CONF_HOST: host}
                )
        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)

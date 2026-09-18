"""Async client for the Raymote (white-label Blynk 2.0) device HTTPS API."""
from __future__ import annotations

import asyncio
import json

import aiohttp

from .const import DEFAULT_HOST, PIN_MODE, PIN_SETPOINT


class RaymoteError(Exception):
    """Communication or API error."""


class RaymoteAuthError(RaymoteError):
    """The device auth token was rejected."""


class RaymoteClient:
    def __init__(self, session: aiohttp.ClientSession, token: str, host: str = DEFAULT_HOST) -> None:
        self._session = session
        self._token = token
        self._host = host.rstrip("/")

    async def _get(self, endpoint: str, **params):
        url = f"{self._host}/external/api/{endpoint}"
        try:
            async with self._session.get(
                url,
                params={"token": self._token, **params},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                body = await resp.text()
                status = resp.status
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise RaymoteError(f"request failed: {err}") from err

        if status >= 400:
            try:
                msg = json.loads(body)["error"]["message"]
            except (ValueError, KeyError, TypeError):
                msg = body[:200]
            if "token" in msg.lower():
                raise RaymoteAuthError(msg)
            raise RaymoteError(f"HTTP {status}: {msg}")
        if not body:
            return None
        try:
            return json.loads(body)
        except ValueError:
            return body

    async def is_connected(self) -> bool:
        return bool(await self._get("isHardwareConnected"))

    async def get_all(self) -> dict:
        pins = await self._get("getAll")
        if not isinstance(pins, dict):
            raise RaymoteError(f"unexpected getAll response: {pins!r}")
        return pins

    async def set_setpoint(self, temp_f: int) -> None:
        await self._get("update", **{PIN_SETPOINT: int(temp_f)})

    async def set_mode(self, mode: int) -> None:
        await self._get("update", **{PIN_MODE: int(mode)})

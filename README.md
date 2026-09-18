# Raypak Raymote for Home Assistant

Unofficial Home Assistant integration for Raypak heat pumps that use the **Raymote** app
(developed against a Crosswind V). Raymote is a white-label [Blynk](https://blynk.io) tenant, so this
talks to the Blynk device HTTPS API at `raymote.raypak.com` using your device's auth token.

Cloud polling, every 30 s. There is no local API on the heater.

> **This controls a real heater.** The integration only ever writes two virtual pins:
> `v67` (mode: off / pool / spa) and `v111` (setpoint, whole °F, checked against the heater's own
> min/max for the active mode). Everything else is read-only. The pin map in
> [PINMAP.md](PINMAP.md) was reverse-engineered on one unit; verify it on yours with
> `blynk_probe.py` before trusting it. Not affiliated with Raypak or Blynk. Use at your own risk.

## What you get

| Entity | Notes |
|---|---|
| `climate` | Off / Heat, presets **pool** and **spa**, target temperature, current water temperature. `hvac_action` comes from the heater's own state code, not from comparing temperatures. |
| Sensors | Water, water inlet/outlet, ambient, coil and discharge temperatures; status text (`No Demand`, `Heating`, ...); compressor starts; Wi-Fi RSSI (disabled by default) |
| Binary sensors | Heating (compressor running), Connected (heater online in the Raymote cloud) |

Turning the climate entity back to *Heat* after *Off* restores the last preset (spa if unknown, e.g. after an HA restart while off).

## Install

**HACS:** HACS → ⋮ → Custom repositories → add `https://github.com/jzabrams/raymote_ha` as type *Integration*, install, restart HA.

**Manual:** copy `custom_components/raymote` into `<config>/custom_components/`, restart HA.

Then *Settings → Devices & services → Add integration → Raypak Raymote* and paste the device auth token.

### Getting the token
Log in at <https://raymote.raypak.com/dashboard/login> with your Raymote app account → open the heater → **Device Info** → Auth Token. Treat it like a password: anyone with it can control the heater.

## Mapping pins on your own unit

```sh
cp .env.example .env        # put RAYMOTE_TOKEN=... in it
./blynk_probe.py            # read-only: polls getAll and prints diffs
```
Change one thing at a time in the Raymote app and watch which pins move. Snapshots are appended to `probe_log.jsonl`.

## Development

```sh
pip install pytest-homeassistant-custom-component
pytest
```

# Crosswind V virtual pin map (work in progress)

Source: `probe_log.jsonl`, mapping session 2026-09-18. Confidence: **C** confirmed by diff, **L** likely, **?** guess.

## Control-related
| Pin | Meaning | Conf | Notes |
|---|---|---|---|
| v67 | mode command: 0=off, 1=pool, 2=spa | C | **writable, verified via API 2026-09-18** (v54 acks within ~3s) |
| v53 | mode (mirror) | C | moves with v67 |
| v54 | mode as reported by heater (use as read-back) | L | consistently lags v67/v53 by ~3s, together with v111/v235/v240 |
| v11 | status bitfield; low bits = mode (0x1010 off / 0x1011 pool / 0x1012 spa) | C | |
| v111 | active setpoint (int, °F) for current mode; **writable, verified via API 2026-09-18** (v43 echoes within ~3s) | C | 95->94->96 on setpoint change; switched to 95 in mode 1 |
| v43 | spa setpoint (float °F), derived from v111 | C | kept 96 while in pool mode |
| v40, v41 | other setpoints (one is probably the pool setpoint = 95) | ? | |
| v235 / v240 | setpoint min / max for current mode | C | 50/104 in spa, 44/95 in pool |
| v42 | 104 = absolute max setpoint | ? | |

## Telemetry
| Pin | Meaning | Conf |
|---|---|---|
| v51, v52 | water temp shown in app (°F) | L |
| v3, v4 | water temp sensors (inlet/outlet) | L |
| v5 | compressor discharge / refrigerant temp: 96->111°F within 60s of start | L |
| v6 | evaporator coil/suction temp: drifts to ambient when idle, dropped 65->55°F on start | L |
| v9 / v10 | ambient air °F / °C | C (same value, two units) |
| v55 | status text: `No Demand`, `Heating` | C |
| v2, v65 | operating state code: 1=idle/no demand, 6=heating | C |
| v12 | output/relay bitfield: 0x007 idle -> 0x287 heating | L |
| v25 | compressor start counter? 18->19 at start, stayed 19 after stop | L |
| v64 | Wi-Fi RSSI dBm | L |
| v19 | slowly rising counter/analog (1286->1310 in 3 min) | ? |
| v50 | noisy 1-5 | ? |
| v148-v199 | fault/alarm flags (all 0) | ? |

## Behaviour
- Start: ~3s after setpoint rises above water temp (v2/v65 1->6, v12 0x007->0x287, v55 `Heating`).
- Stop: ~68s after setpoint dropped below water temp (16:30:02 -> 16:31:10); direct 6->1, no intermediate state seen. Judge "running" from v65, not setpoint vs temp.

## Unknown / untested
Setpoint write via `update?v111=N` verified (92->91->92, v43 acked each).
Mode write via `update?v67=N` verified (spa->pool->off->spa, v54 acked each within 3s).

"""Constants for the Raypak Raymote integration. Pin meanings: see PINMAP.md."""

DOMAIN = "raymote"
DEFAULT_HOST = "https://raymote.raypak.com"
SCAN_INTERVAL_SECONDS = 30
# The heater acknowledges a write (v54 / v43 follow v67 / v111) about 3s later.
WRITE_ACK_DELAY_SECONDS = 4

CONF_HOST = "host"
CONF_TOKEN = "token"

# The only pins this integration ever writes.
PIN_MODE = "v67"
PIN_SETPOINT = "v111"

PIN_MODE_ACK = "v54"
PIN_STATE = "v65"
PIN_STATUS_TEXT = "v55"
PIN_SETPOINT_MIN = "v235"
PIN_SETPOINT_MAX = "v240"
PIN_WATER_TEMP = "v51"

MODE_OFF = 0
MODE_POOL = 1
MODE_SPA = 2
PRESETS = {MODE_POOL: "pool", MODE_SPA: "spa"}

STATE_HEATING = 6

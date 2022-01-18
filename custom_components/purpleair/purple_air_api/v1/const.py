"""Constants for the v1 PurpleAir API."""

from __future__ import annotations

from typing import Final

URL_API_V1_KEYS_URL: Final = "https://api.purpleair.com/v1/keys"

URL_API_V1_SENSOR: Final = "https://api.purpleair.com/v1/sensors/{pa_sensor_id}"

URL_API_V1_SENSORS: Final = "https://api.purpleair.com/v1/sensors"

API_INT_VALUES: Final = [
    "rssi",
    "uptime",
    "confidence",
    "humidity",
    "temperature",
]

API_FLOAT_VALUES: Final = [
    "latitude",
    "longitude",
    "pm1.0_atm",
    "pm2.5_atm",
    "pm2.5_cf_1,",
    "pm10.0_atm",
    "pressure",
]

API_STRING_VALUES: Final = [
    "model",
    "hardware",
    "firmware_version",
    "firmware_upgrade",
]

API_SPECIAL_VALUES: Final = [
    "location_type",
    "private",
    "channel_state",
    "channel_flags",
]

API_TIMESTAMP_VALUES: Final = [
    "last_seen",
]

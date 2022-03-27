"""Constants for the v1 PurpleAir API."""

from __future__ import annotations

from typing import Final

URL_API_V1_KEYS_URL: Final = "https://api.purpleair.com/v1/keys"

URL_API_V1_SENSOR: Final = "https://api.purpleair.com/v1/sensors/{pa_sensor_id}"

URL_API_V1_SENSORS: Final = "https://api.purpleair.com/v1/sensors"

API_SENSOR_FIELDS: Final = {
    "sensor_index": -1,
    "rssi": -1,
    "analog_input": -1,
    "last_seen": -1,
    "channel_state": -1,
    "channel_flags": -1,
    "confidence": -1,
    "humidity": -1,
    "temperature": -1,
    "pressure": -1,
    "pm1.0_atm": -1,
    "pm2.5_atm": -1,
    "pm2.5_cf_1": -1,
    "pm10.0_atm": -1,
    "uptime": -1,
}

API_DEVICE_FIELDS: Final = {
    "model": -1,
    "hardware": -1,
    "location_type": -1,
    "private": -1,
    "latitude": -1,
    "longitude": -1,
    "firmware_version": -1,
    "firmware_upgrade": -1,
}

API_INT_VALUES: Final = [
    "rssi",
    "uptime",
    "confidence",
    "humidity",
    "temperature",
]

API_FLOAT_VALUES: Final = [
    "analog_input",
    "latitude",
    "longitude",
    "pm1.0_atm",
    "pm2.5_atm",
    "pm2.5_cf_1",
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

API_VALUES: Final = set(
    API_INT_VALUES
    + API_FLOAT_VALUES
    + API_STRING_VALUES
    + API_SPECIAL_VALUES
    + API_TIMESTAMP_VALUES
)

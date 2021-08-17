"""Constants for the Purple Air integration."""
from __future__ import annotations
from typing import Final

from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
)

from .model import PurpleAirSensorEntityDescription

AQI_BREAKPOINTS = {
    'pm2_5': [
        {'pm_low': 500.5, 'pm_high': 999.9, 'aqi_low': 501, 'aqi_high': 999},  # noqa: E241
        {'pm_low': 350.5, 'pm_high': 500.4, 'aqi_low': 401, 'aqi_high': 500},  # noqa: E241
        {'pm_low': 250.5, 'pm_high': 350.4, 'aqi_low': 301, 'aqi_high': 400},  # noqa: E241
        {'pm_low': 150.5, 'pm_high': 250.4, 'aqi_low': 201, 'aqi_high': 300},  # noqa: E241
        {'pm_low':  55.5, 'pm_high': 150.4, 'aqi_low': 151, 'aqi_high': 200},  # noqa: E241
        {'pm_low':  35.5, 'pm_high':  55.4, 'aqi_low': 101, 'aqi_high': 150},  # noqa: E241
        {'pm_low':  12.1, 'pm_high':  35.4, 'aqi_low':  51, 'aqi_high': 100},  # noqa: E241
        {'pm_low':     0, 'pm_high':  12.0, 'aqi_low':   0, 'aqi_high':  50},  # noqa: E241
    ],
}

DISPATCHER_PURPLE_AIR = 'dispatcher_purple_air'

DOMAIN = 'purpleair'

JSON_PROPERTIES = ['pm1_0_atm', 'pm2_5_atm', 'pm10_0_atm']

PRIVATE_URL = 'https://www.purpleair.com/json?show={nodes}&key={key}'

PUBLIC_URL = 'https://www.purpleair.com/json?show={nodes}'

SCAN_INTERVAL = 300

SENSOR_TYPES: tuple[PurpleAirSensorEntityDescription, ...] = (
#    PurpleAirSensorEntityDescription(
#        key='PM25',
#        icon='mdi:blur',
#        name='PM2.5',
#        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
#        state_class=STATE_CLASS_MEASUREMENT,
#        unique_id_suffix='pm25',
#    ),
    PurpleAirSensorEntityDescription(
        key='pm2_5_atm_aqi',
        icon='mdi:weather-hazy',
        name='Air Quality Index',
        native_unit_of_measurement='AQI',
        state_class=STATE_CLASS_MEASUREMENT,
        unique_id_suffix='air_quality_index',
    ),
)

"""Constants for the Purple Air integration."""
from __future__ import annotations
from typing import Final

from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    DEVICE_CLASS_AQI,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_PM1,
    DEVICE_CLASS_PM10,
    DEVICE_CLASS_PM25,
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_TEMPERATURE,
    PERCENTAGE,
    PRESSURE_HPA,
    TEMP_FAHRENHEIT,
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

API_ATTR_PM1: Final = 'pm1_0_atm'
API_ATTR_PM10: Final = 'pm10_0_atm'
API_ATTR_PM25: Final = 'pm2_5_atm'
API_ATTR_PM25_AQI: Final = 'pm2_5_atm_aqi'
API_ATTR_HUMIDITY: Final = 'humidity'
API_ATTR_TEMP_F: Final = 'temp_f'
API_ATTR_PRESSURE: Final = 'pressure'

DOMAIN: Final = 'purpleair'

JSON_PROPERTIES: Final = [
    API_ATTR_PM1, API_ATTR_PM25, API_ATTR_PM10, API_ATTR_HUMIDITY, API_ATTR_TEMP_F,
    API_ATTR_PRESSURE
]

PRIVATE_URL: Final = 'https://www.purpleair.com/json?show={nodes}&key={key}'

PUBLIC_URL: Final = 'https://www.purpleair.com/json?show={nodes}'

SCAN_INTERVAL: Final = 300

SENSOR_TYPES: tuple[PurpleAirSensorEntityDescription, ...] = (
    PurpleAirSensorEntityDescription(
        key=API_ATTR_PM25_AQI,
        name='Air Quality Index',
        icon='mdi:weather-hazy',
        device_class=DEVICE_CLASS_AQI,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement='AQI',
        unique_id_suffix='air_quality_index',
        enable_default=True,
        primary=True,
    ),
    PurpleAirSensorEntityDescription(
        key=API_ATTR_PM25,
        name='PM 2.5',
        icon='mdi:blur',
        device_class=DEVICE_CLASS_PM25,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unique_id_suffix='pm25',
    ),
    PurpleAirSensorEntityDescription(
        key=API_ATTR_PM1,
        name='PM 1.0',
        icon='mdi:blur',
        device_class=DEVICE_CLASS_PM1,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unique_id_suffix='pm1',
    ),
    PurpleAirSensorEntityDescription(
        key=API_ATTR_PM10,
        name='PM 10.0',
        icon='mdi:blur',
        device_class=DEVICE_CLASS_PM10,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unique_id_suffix='pm10',
    ),
    PurpleAirSensorEntityDescription(
        key=API_ATTR_HUMIDITY,
        name='Humidity',
        icon='mdi:water-percent',
        device_class=DEVICE_CLASS_HUMIDITY,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        unique_id_suffix='humidity',
    ),
    PurpleAirSensorEntityDescription(
        key=API_ATTR_TEMP_F,
        name='Temperature',
        icon='mdi:thermometer',
        device_class=DEVICE_CLASS_TEMPERATURE,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement=TEMP_FAHRENHEIT,
        unique_id_suffix='temp',
    ),
    PurpleAirSensorEntityDescription(
        key=API_ATTR_PRESSURE,
        name='Pressure',
        icon='mdi:gauge',
        device_class=DEVICE_CLASS_PRESSURE,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement=PRESSURE_HPA,
        unique_id_suffix='pressure',
    ),
)

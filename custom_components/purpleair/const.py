# pylint: disable=unexpected-keyword-arg
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
from .purple_air_api.const import (
    API_ATTR_PM1,
    API_ATTR_PM10,
    API_ATTR_PM25,
    API_ATTR_PM25_AQI,
    API_ATTR_PM25_AQI_RAW,
    API_ATTR_HUMIDITY,
    API_ATTR_TEMP_F,
    API_ATTR_PRESSURE,
)

DOMAIN: Final = 'purpleair'

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
        key=API_ATTR_PM25_AQI_RAW,
        name='Air Quality Index (Raw)',
        icon='mdi:weather-hazy',
        device_class=DEVICE_CLASS_AQI,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement='AQI',
        unique_id_suffix='aqi_raw',
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

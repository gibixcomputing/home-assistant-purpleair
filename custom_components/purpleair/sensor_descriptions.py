"""Defines sensor entity descriptions for v1 sensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfTemperature,
)


@dataclass
class PASensorDescription(SensorEntityDescription):
    """Extra properties."""

    attr_name: str | None = None


AqiSensorDescription = PASensorDescription(
    "air_quality_index",
    name="Air Quality Index",
    icon="mdi:weather-hazy",
    device_class=SensorDeviceClass.AQI,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=None,
    entity_registry_enabled_default=True,
)

SIMPLE_SENSOR_DESCRIPTIONS: Final = [
    PASensorDescription(
        "aqi_raw",
        name="Air Quality Index (Raw)",
        icon="mdi:weather-hazy",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=None,
        entity_registry_enabled_default=False,
        attr_name="pm2_5_aqi_instant",
    ),
    PASensorDescription(
        "pm25",
        name="PM 2.5",
        icon="mdi:blur",
        device_class=SensorDeviceClass.PM25,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        entity_registry_enabled_default=False,
        attr_name="pm2_5_atm",
    ),
    PASensorDescription(
        "pm1",
        name="PM 1.0",
        icon="mdi:blur",
        device_class=SensorDeviceClass.PM1,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        entity_registry_enabled_default=False,
        attr_name="pm1_0_atm",
    ),
    PASensorDescription(
        "pm10",
        name="PM 10.0",
        icon="mdi:blur",
        device_class=SensorDeviceClass.PM10,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        entity_registry_enabled_default=False,
        attr_name="pm10_0_atm",
    ),
    PASensorDescription(
        "humidity",
        name="Humidity",
        icon="mdi:water-percent",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_registry_enabled_default=False,
        attr_name="humidity",
    ),
    PASensorDescription(
        "temp",
        name="Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        entity_registry_enabled_default=False,
        attr_name="temperature",
    ),
    PASensorDescription(
        "pressure",
        name="Pressure",
        icon="mdi:gauge",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.HPA,
        entity_registry_enabled_default=False,
        attr_name="pressure",
    ),
]

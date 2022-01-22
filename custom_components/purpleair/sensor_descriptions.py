"""Defines sensor entity descriptions for v1 sensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    SensorEntityDescription,
)
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


@dataclass
class PASensorDescription(SensorEntityDescription):
    """Extra properties."""

    attr_name: str | None = None


AqiSensorDescription = PASensorDescription(  # type: ignore
    "air_quality_index",
    name="Air Quality Index",
    icon="mdi:weather-hazy",
    device_class=DEVICE_CLASS_AQI,
    state_class=STATE_CLASS_MEASUREMENT,
    native_unit_of_measurement="AQI",
    entity_registry_enabled_default=True,
)

SIMPLE_SENSOR_DESCRIPTIONS: Final = [
    PASensorDescription(  # type: ignore
        "aqi_raw",
        name="Air Quality Index (Raw)",
        icon="mdi:weather-hazy",
        device_class=DEVICE_CLASS_AQI,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement="AQI",
        attr_name="pm2_5_aqi_instant",
    ),
    PASensorDescription(  # type: ignore
        "pm25",
        name="PM 2.5",
        icon="mdi:blur",
        device_class=DEVICE_CLASS_PM25,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        attr_name="pm2_5_atm",
    ),
    PASensorDescription(  # type: ignore
        "pm1",
        name="PM 1.0",
        icon="mdi:blur",
        device_class=DEVICE_CLASS_PM1,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        attr_name="pm1_0_atm",
    ),
    PASensorDescription(  # type: ignore
        "pm10",
        name="PM 10.0",
        icon="mdi:blur",
        device_class=DEVICE_CLASS_PM10,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        attr_name="pm10_0_atm",
    ),
    PASensorDescription(  # type: ignore
        "humidity",
        name="Humidity",
        icon="mdi:water-percent",
        device_class=DEVICE_CLASS_HUMIDITY,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        attr_name="humidity",
    ),
    PASensorDescription(  # type: ignore
        "temp",
        name="Temperature",
        icon="mdi:thermometer",
        device_class=DEVICE_CLASS_TEMPERATURE,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement=TEMP_FAHRENHEIT,
        attr_name="temperature",
    ),
    PASensorDescription(  # type: ignore
        "pressure",
        name="Pressure",
        icon="mdi:gauge",
        device_class=DEVICE_CLASS_PRESSURE,
        state_class=STATE_CLASS_MEASUREMENT,
        native_unit_of_measurement=PRESSURE_HPA,
        attr_name="pressure",
    ),
]

"""Defines sensor entity descriptions for v1 sensors."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    SensorEntityDescription,
)
from homeassistant.const import DEVICE_CLASS_AQI


@dataclass
class PASensorDescription(SensorEntityDescription):
    """Extra properties."""

    suffix: str | None = None


AqiSensorDescription = PASensorDescription(  # type: ignore
    "aqi",
    name="Air Quality Index",
    icon="mdi:weather-hazy",
    device_class=DEVICE_CLASS_AQI,
    state_class=STATE_CLASS_MEASUREMENT,
    native_unit_of_measurement="AQI",
    entity_registry_enabled_default=True,
    suffix="air_quality_index",
)

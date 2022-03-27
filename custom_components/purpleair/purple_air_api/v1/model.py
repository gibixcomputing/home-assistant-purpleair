"""Models for the v1 PurpleAir API."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import logging
from typing import Deque, Dict, Literal, TypedDict, Union

from .const import API_VALUES

SENSOR_READING_ADDITIONAL_ATTRIBUTES = [
    "pm2_5_aqi_instant",
    "pm2_5_aqi_epa",
    "pm2_5_aqi_epa_status",
]

SensorReadingAdditionalAttrsType = Union[
    Literal["pm2_5_aqi_instant"],
    Literal["pm2_5_aqi_epa"],
    Literal["pm2_5_aqi_epa_status"],
]

_LOGGER = logging.getLogger(__name__)


@dataclass
class AqiBreakpoint:
    """Describes a breakpoint for calculating AQI.

    Attributes:
        pm_low   -- The low end of particulate matter in ugm3
        pm_high  -- The high end of particulate matter in ugm3
        aqi_low  -- The low end of the calculated AQI
        aqi_high -- The high end of the calculated AQI
    """

    pm_low: float
    pm_high: float
    aqi_low: float
    aqi_high: float


@dataclass
class ApiConfigEntry:
    """Describes a configuration entry for the PurpleAir v1 API.

    Attributes:
      pa_sensor_id: ID of the sensor being configured.
      name: Name of the sensor.
      hidden: Flag indicating whether the sensor is private or public.
      read_key: Sensor read key used when retrieving data from a hidden sensor.
    """

    pa_sensor_id: str
    name: str
    hidden: bool
    read_key: str | None = None


@dataclass
class DeviceReading:
    """Holds device data for a PurpleAir Sensor."""

    pa_sensor_id: str

    latitude: float | None = None
    longitude: float | None = None
    model: str | None = None
    hardware: str | None = None
    firmware_version: str | None = None
    firmware_upgrade: str | None = None
    location_type: str | None = None
    private: bool | None = None

    def set_value(self, name: str, value: int | float | str | datetime | None):
        """Set the field to the provided value, if it exists."""

        # sanity check the field names match known values first.
        if name not in API_VALUES:
            _LOGGER.debug(
                "requested field, %s, does not exist in API_VALUES (DeviceReading)",
                name,
            )
            return

        # incoming field names may have sensor attributes, so this isn't an error.
        normalized_value = name.replace(".", "_")
        if not hasattr(self, normalized_value):
            return

        setattr(self, normalized_value, value)


@dataclass
class EpaAvgValue:
    """Provides values for the EPA value cache.

    Attributes:
        hum  -- List of last humidity readings
        pm25 -- List of last PM2.5 CF=1 readings
        timestamp -- Date the value reading was created
    """

    hum: float
    pm25: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


EpaAvgValueCache = Dict[str, Deque[EpaAvgValue]]


class NormalizedApiData(TypedDict):
    """Holds normalized sensor data."""

    sensor: SensorReading
    device: DeviceReading | None


@dataclass
class SensorReading:
    """Holds sensor data for a PurpleAir Sensor."""

    pa_sensor_id: str

    rssi: int | None = None
    uptime: int | None = None
    confidence: int | None = None
    humidity: int | None = None
    temperature: float | None = None

    analog_input: float | None = None
    pm1_0_atm: float | None = None
    pm2_5_atm: float | None = None
    pm2_5_cf_1: float | None = None
    pm10_0_atm: float | None = None
    pressure: float | None = None

    channel_flags: str | None = None
    channel_state: str | None = None
    last_seen: datetime | None = None

    # additional attributes
    pm2_5_aqi_instant: int | None = None
    pm2_5_aqi_epa: int | None = None
    pm2_5_aqi_epa_status: str | None = None

    def set_value(self, name: str, value: int | float | str | datetime | None):
        """Set the field to the provided value, if it exists."""

        # sanity check the field names match known values first.
        if name not in API_VALUES:
            _LOGGER.debug(
                "requested field, %s, does not exist in API_VALUES (SensorReading)",
                name,
            )
            return

        # incoming field names may have device attributes, so this isn't an error.
        normalized_name = name.replace(".", "_")
        if not hasattr(self, normalized_name):
            return

        setattr(self, normalized_name, value)

    def set_additional_value(
        self, name: SensorReadingAdditionalAttrsType, value: int | str | None
    ) -> None:
        """Set the additional field to the provided value."""

        if name not in SENSOR_READING_ADDITIONAL_ATTRIBUTES:
            _LOGGER.error("Got request for unknown additional field: %s", name)
            return

        setattr(self, name, value)

"""Models for the v1 PurpleAir API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from typing import TypedDict

from .const import API_VALUES

_LOGGER = logging.getLogger(__name__)


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
class SensorReading:
    """Holds sensor data for a PurpleAir Sensor."""

    pa_sensor_id: str

    rssi: int | None = None
    uptime: int | None = None
    confidence: int | None = None
    humidity: int | None = None
    temperature: float | None = None

    pm1_0_atm: float | None = None
    pm2_5_atm: float | None = None
    pm2_5_cf_1: float | None = None
    pm10_0_atm: float | None = None
    pressure: float | None = None

    channel_flags: str | None = None
    channel_state: str | None = None
    last_seen: datetime | None = None

    def set_value(self, field: str, value: int | float | str | datetime | None):
        """Set the field to the provided value, if it exists."""

        # sanity check the field names match known values first.
        if field not in API_VALUES:
            _LOGGER.debug(
                "requested field, %s, does not exist in API_VALUES (SensorReading)",
                field,
            )
            return

        # incoming field names may have device attributes, so this isn't an error.
        normalized_value = field.replace(".", "_")
        if not hasattr(self, normalized_value):
            return

        setattr(self, normalized_value, value)


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

    def set_value(self, field: str, value: int | float | str | datetime | None):
        """Set the field to the provided value, if it exists."""

        # sanity check the field names match known values first.
        if field not in API_VALUES:
            _LOGGER.debug(
                "requested field, %s, does not exist in API_VALUES (DeviceReading)",
                field,
            )
            return

        # incoming field names may have device attributes, so this isn't an error.
        normalized_value = field.replace(".", "_")
        if not hasattr(self, normalized_value):
            return

        setattr(self, normalized_value, value)


class NormalizedApiData(TypedDict):
    """Holds normalized sensor data."""

    sensor: SensorReading
    device: DeviceReading | None

"""Provides models for the PurpleAir API."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PurpleAirApiConfigEntry:
    """Describes a configuration entry for the PurpleAir API.

    Attributes:
        node_id -- The ID of the sensor being configured
        title   -- The title of the sensor
        hidden  -- Flag indicating whether the sensor is private or public
        key     -- Key used when retrieving sensor data. Required if the hidden attribute is True.
    """
    node_id: str
    title: str
    hidden: bool
    key: Optional[str] = None


@dataclass
class PurpleAirSensorData:  # pylint: disable=too-many-instance-attributes
    """Represents parsed individual sensor information from the PurpleAir API.

    Attributes:
        pa_sensor_id    -- Registered ID of the PurleAir Sensor
        label           -- API user-defined name of the sensor.
        last_seen       -- Date and time the sensor was last seen according to the API.
        last_update     -- Date and time the sensor last updated according to the API.
        readings        -- Dictonary holding the computed sensor reading data.
        device_location -- Location of the sensor (currently 'indoor', 'outdoor', or 'unknown').
        version         -- Firmware version of the sensor.
        type            -- Type of the air quality sensors in the PurpleAir sensor.
        lat             -- Latitude of the sensor.
        lon             -- Longitude of the sensor.
        rssi            -- Current reported RSSI WiFi signal strength.
        adc             -- Current reported ADC voltage of the sensor.
        uptime          -- Current uptime reported by the sensor.
    """
    pa_sensor_id: str
    label: str
    last_seen: datetime
    last_update: datetime
    readings: dict = field(default_factory=dict)
    device_location: str = 'unknown'
    version: str = 'unknown'
    type: str = 'unknown'
    lat: Optional[float] = None
    lon: Optional[float] = None
    rssi: float = 0
    adc: float = 0
    uptime: int = 0


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


EpaAvgValueCache = dict[str, deque[EpaAvgValue]]

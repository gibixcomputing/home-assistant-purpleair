"""Provides models for the PurpleAir API."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime


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
    key: str = None


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

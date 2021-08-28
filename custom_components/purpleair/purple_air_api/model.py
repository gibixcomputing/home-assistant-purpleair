"""Provides models for the PurpleAir API."""
from dataclasses import dataclass
from typing import List, TypedDict


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


class EpaAvgValues(TypedDict):
    """Provides guidance for the data in the EPA_AVG_DATA dictionary.

    Attributes:
        hum  -- List of last humidity readings
        pm25 -- List of last PM2.5 CF=1 readings
    """
    hum: List[float]
    pm25: List[float]

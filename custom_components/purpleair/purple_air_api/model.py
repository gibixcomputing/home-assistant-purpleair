"""Provides models for the PurpleAir API."""
from dataclasses import dataclass


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

"""Define AQI breakpoints."""
# required to prevent circular dependency
from __future__ import annotations

from .model import AqiBreakpoint

AQI_BREAKPOINTS = {
    "pm2_5": [
        AqiBreakpoint(pm_low=500.5, pm_high=999.9, aqi_low=501, aqi_high=999),
        AqiBreakpoint(pm_low=500.5, pm_high=999.9, aqi_low=501, aqi_high=999),
        AqiBreakpoint(pm_low=350.5, pm_high=500.4, aqi_low=401, aqi_high=500),
        AqiBreakpoint(pm_low=250.5, pm_high=350.4, aqi_low=301, aqi_high=400),
        AqiBreakpoint(pm_low=150.5, pm_high=250.4, aqi_low=201, aqi_high=300),
        AqiBreakpoint(pm_low=55.5, pm_high=150.4, aqi_low=151, aqi_high=200),
        AqiBreakpoint(pm_low=35.5, pm_high=55.4, aqi_low=101, aqi_high=150),
        AqiBreakpoint(pm_low=12.1, pm_high=35.4, aqi_low=51, aqi_high=100),
        AqiBreakpoint(pm_low=0, pm_high=12.0, aqi_low=0, aqi_high=50),
    ],
}

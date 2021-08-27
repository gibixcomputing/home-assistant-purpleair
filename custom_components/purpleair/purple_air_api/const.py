"""Constants for the PurpleAir API."""
from __future__ import annotations
from typing import Final

from .model import AqiBreakpoint

AQI_BREAKPOINTS = {
    'pm2_5': [
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

API_ATTR_PM1: Final = 'pm1_0_atm'
API_ATTR_PM10: Final = 'pm10_0_atm'
API_ATTR_PM25: Final = 'pm2_5_atm'
API_ATTR_PM25_AQI: Final = 'pm2_5_atm_aqi'
API_ATTR_HUMIDITY: Final = 'humidity'
API_ATTR_TEMP_F: Final = 'temp_f'
API_ATTR_PRESSURE: Final = 'pressure'

JSON_PROPERTIES: Final = [
    API_ATTR_PM1, API_ATTR_PM25, API_ATTR_PM10, API_ATTR_HUMIDITY, API_ATTR_TEMP_F,
    API_ATTR_PRESSURE
]

PRIVATE_URL: Final = 'https://www.purpleair.com/json?show={nodes}&key={key}'

PUBLIC_URL: Final = 'https://www.purpleair.com/json?show={nodes}'

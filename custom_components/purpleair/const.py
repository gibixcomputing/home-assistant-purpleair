"""Constants for the Purple Air integration."""

AQI_BREAKPOINTS = {
    'pm2_5': [
        {'pm_low': 500.5, 'pm_high': 999.9, 'aqi_low': 501, 'aqi_high': 999},  # noqa: E241
        {'pm_low': 350.5, 'pm_high': 500.4, 'aqi_low': 401, 'aqi_high': 500},  # noqa: E241
        {'pm_low': 250.5, 'pm_high': 350.4, 'aqi_low': 301, 'aqi_high': 400},  # noqa: E241
        {'pm_low': 150.5, 'pm_high': 250.4, 'aqi_low': 201, 'aqi_high': 300},  # noqa: E241
        {'pm_low':  55.5, 'pm_high': 150.4, 'aqi_low': 151, 'aqi_high': 200},  # noqa: E241
        {'pm_low':  35.5, 'pm_high':  55.4, 'aqi_low': 101, 'aqi_high': 150},  # noqa: E241
        {'pm_low':  12.1, 'pm_high':  35.4, 'aqi_low':  51, 'aqi_high': 100},  # noqa: E241
        {'pm_low':     0, 'pm_high':  12.0, 'aqi_low':   0, 'aqi_high':  50},  # noqa: E241
    ],
}

DISPATCHER_PURPLE_AIR = 'dispatcher_purple_air'

DOMAIN = "purpleair"

JSON_PROPERTIES = ['pm1_0_atm', 'pm2_5_atm', 'pm10_0_atm']

PRIVATE_URL = "https://www.purpleair.com/json?show={nodes}&key={key}"

PUBLIC_URL = "https://www.purpleair.com/json?show={nodes}"

SCAN_INTERVAL = 300

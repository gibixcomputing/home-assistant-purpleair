"""Utility functions for the v1 PurpleAir API."""
from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta
from http import HTTPStatus
import logging
from math import fsum

from aiohttp import ClientResponse, ClientSession

from .aqi_breakpoints import AQI_BREAKPOINTS
from .const import URL_API_V1_KEYS_URL, URL_API_V1_SENSOR
from .exceptions import PurpleAirApiConfigError
from .model import (
    ApiConfigEntry,
    EpaAvgValue,
    EpaAvgValueCache,
    NormalizedApiData,
    SensorReading,
)

_LOGGER = logging.getLogger(__name__)


def add_aqi_calculations(
    sensors: dict[str, NormalizedApiData], *, cache: EpaAvgValueCache
) -> None:
    """
    Add AQI calculations as custom properties to the readings.

    This computes the AQI values by calculating them based off the corrections
    and breakpoints, providing a few variations depending what is available.
    """

    for sensor_data in sensors.values():
        sensor = sensor_data["sensor"]
        if sensor.pm2_5_atm is not None:
            instant_aqi = calc_aqi(sensor.pm2_5_atm, "pm2_5")
            sensor.set_additional_value("pm2_5_aqi_instant", instant_aqi)

        # If we have the PM2.5 CF=1 and humidity data, we can calculate AQI using the EPA
        # corrections that were identified to better calibrate PurpleAir sensors to the EPA NowCast
        # AQI formula. This was identified during the 2020 wildfire season and better represents AQI
        # with wildfire smoke for the unhealthy for sensitive groups/unhealthy for everyone AQI
        # breakpoints. Unlike the raw AQI sensor, this is averaged over the last hour. For
        # simplicity, this is applied here as a rolling hour average and provides instant results as
        # readings are provided. Readings over an hour old will be removed from the cache.
        #
        # The formula is identified as: PM2.5 corrected= 0.534*[PA_cf1(avgAB)] - 0.0844*RH +5.604
        # NOTE: we check for None explicitly since 0 is a valid number
        if sensor.pm2_5_cf_1 is not None and sensor.humidity is not None:
            epa_avg = cache[sensor.pa_sensor_id]
            epa_avg.append(EpaAvgValue(hum=sensor.humidity, pm25=sensor.pm2_5_cf_1))

            _clean_expired_cache_entries(sensor, epa_avg)

            humidity_avg = round(fsum(v.hum for v in epa_avg) / len(epa_avg), 5)
            pm25cf1_avg = round(fsum(v.pm25 for v in epa_avg) / len(epa_avg), 5)

            # See https://www.epa.gov/sites/default/files/2021-05/documents/toolsresourceswebinar_purpleairsmoke_210519b.pdf
            pm25_corrected = (0.52 * pm25cf1_avg) - (0.086 * humidity_avg) + 5.75
            if pm25cf1_avg > 343:
                pm25_corrected = (
                    (0.46 * pm25cf1_avg) + (3.93e-4 * pm25cf1_avg * pm25cf1_avg) + 2.97
                )
            pm25_corrected = round(max(0, pm25_corrected), 1)
            pm25_corrected_aqi = calc_aqi(pm25_corrected, "pm2_5")

            _LOGGER.debug(
                "(%s): EPA correction: (pm25: %s, hum: %s, corrected: %s, aqi: %s)",
                sensor.pa_sensor_id,
                pm25cf1_avg,
                humidity_avg,
                pm25_corrected,
                pm25_corrected_aqi,
            )

            aqi_status = "stable"
            count = len(epa_avg)
            if count < 12:
                aqi_status = f"calculating ({(12 - count) * 5} mins left)"

            sensor.set_additional_value("pm2_5_aqi_epa", pm25_corrected_aqi)
            sensor.set_additional_value("pm2_5_aqi_epa_status", aqi_status)


def apply_sensor_corrections(sensors: dict[str, NormalizedApiData]) -> None:
    """
    Apply corrections to incoming sensor data using known adjustment values.

    The sensors for temperature and humidity are known to be slightly outside of
    real values, this will apply a blanket correction of subtracting 8°F from the
    temperature and adding 4% to the humidity value. This is documented as the
    average variance for those two sensor values.

    From the docs:
    - Humidity:
        Relative humidity inside of the sensor housing (%). On average, this is
        4% lower than ambient conditions. Null if not equipped.
    - Temperature:
        Temperature inside of the sensor housing (F). On average, this is 8F
        higher than ambient conditions. Null if not equipped.
    """

    for sensor_data in sensors.values():
        sensor = sensor_data["sensor"]
        if temperature := sensor.temperature:
            sensor.temperature = temperature - 8
            _LOGGER.debug(
                "applied temperature correction from %s to %s",
                temperature,
                sensor.temperature,
            )

        if humidity := sensor.humidity:
            sensor.humidity = humidity + 4
            _LOGGER.debug(
                "applied humidity correction from %s to %s", humidity, sensor.humidity
            )


def calc_aqi(value: float, index: str) -> int | None:
    """
    Calculate the air quality index based off the available conversion data.

    This uses the sensors current Particulate Matter 2.5 value. Returns an AQI
    between 0 and 999 or None if the sensor reading is invalid.

    See AQI_BREAKPOINTS in const.py.
    """

    if index not in AQI_BREAKPOINTS:
        _LOGGER.debug("calc_aqi requested for unknown type: %s", index)
        return None

    aqi_bp_index = AQI_BREAKPOINTS[index]
    aqi_bp = next((bp for bp in aqi_bp_index if bp.pm_low <= value <= bp.pm_high), None)

    if not aqi_bp:
        _LOGGER.debug("value %s did not fall in valid range for type %s", value, index)
        return None

    aqi_range = aqi_bp.aqi_high - aqi_bp.aqi_low
    pm_range = aqi_bp.pm_high - aqi_bp.pm_low
    aqi_c = value - aqi_bp.pm_low
    return round((aqi_range / pm_range) * aqi_c + aqi_bp.aqi_low)


def create_epa_value_cache() -> EpaAvgValueCache:
    """Create a new, empty EPA value cache."""
    cache: EpaAvgValueCache = defaultdict(lambda: deque(maxlen=12))
    return cache


async def get_api_sensor_config(
    session: ClientSession,
    api_key: str,
    pa_sensor_id: str,
    pa_sensor_read_key: str = None,
) -> ApiConfigEntry:
    """
    Get a new configuration for the sensor with the provided information.

    Provide your PurpleAir API READ key in `api_key` and the sensor to configure
    via `pa_sensor_id`. If the sensor is private (hidden) a read key must be
    provided in the `pa_sensor_read_key` parameter. This method will either return
    a valid PurpleAirApiConfigEntry with the sensor configuration data or will
    raise a PurpleAirApiConfigError exception describing what went wrong.

    Possible error combinations:

    |--------------|--------------|----------------------------------------------|
    | .param       | .extra       |                                              |
    |--------------|--------------|----------------------------------------------|
    | api_key      | missing      | The parameter is missing.                    |
    |              | bad_status   | PA server returned a bad status.             |
    |              | not_read_key | PA server indicated key is not a READ key.   |
    |              | forbidden    | The key is invalid or restricted.            |
    |--------------|--------------|----------------------------------------------|
    | server_error | str          | .extra is the HTTP reason string.            |
    |--------------|--------------|----------------------------------------------|
    | pa_sensor_id | missing      | The parameter is missing.                    |
    |              | not_found    | The PA sensor was not found. Does it need a  |
    |              |              | read key because it's hidden?                |
    |              | bad_read_key | pa_sensor_read_key does not match sensor     |
    |              |              | read key.                                    |
    |--------------|--------------|----------------------------------------------|
    | bad_request  | str          | PA server returned bad request.              |
    |              |              | .extra holds the reason.                     |
    |--------------|--------------|----------------------------------------------|
    """

    if not isinstance(api_key, str):
        raise PurpleAirApiConfigError("api_key", "missing")

    if not isinstance(pa_sensor_id, str):
        raise PurpleAirApiConfigError("pa_sensor_id", "missing")

    headers = {
        "Accept": "application/json",
        "X-API-Key": api_key,
    }

    async with session.get(URL_API_V1_KEYS_URL, headers=headers) as resp:
        if resp.status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            _LOGGER.error(
                "(get_api_sensor_config[key_fetch]) PurpleAir reported a server error: %s",
                resp.reason,
            )
            raise PurpleAirApiConfigError("server_error", resp.reason)

        key_data = await resp.json()
        _LOGGER.debug("(get_api_sensor_config[key_fetch]) key response: %s", key_data)

        if not resp.ok:
            if resp.status == HTTPStatus.FORBIDDEN:
                _LOGGER.error(
                    "PurpleAir API reported key '%s' as invalid or restricted: %s",
                    api_key,
                    key_data,
                )
                raise PurpleAirApiConfigError("api_key", "forbidden")

            raise PurpleAirApiConfigError("api_key", "bad_status")

        if key_data.get("api_key_type") != "READ":
            raise PurpleAirApiConfigError("api_key", "not_read_key")

    config_fields = [
        "name",
        "primary_key_a",
        "private",
    ]

    url = URL_API_V1_SENSOR.format(pa_sensor_id=pa_sensor_id)
    params = {"fields": ",".join(config_fields)}

    if pa_sensor_read_key:
        params["read_key"] = str(pa_sensor_read_key)

    async with session.get(url, headers=headers, params=params) as resp:
        sensor_data = await _get_sensor_data_from_api(resp)

    hidden = int(sensor_data.get("private", 0)) == 1

    config = ApiConfigEntry(
        pa_sensor_id=str(sensor_data.get("sensor_index")),
        name=str(sensor_data.get("name")),
        hidden=hidden,
        read_key=str(sensor_data.get("primary_key_a")) if hidden else None,
    )

    _LOGGER.debug("(get_api_sensor_config) generated configuration: %s", config)

    return config


async def _get_sensor_data_from_api(resp: ClientResponse) -> dict:
    # don't parse as json if > HTTP 500
    if resp.status >= HTTPStatus.INTERNAL_SERVER_ERROR:
        _LOGGER.error(
            "(get_api_sensor_config) PurpleAir reported a server error: %s", resp.reason
        )
        raise PurpleAirApiConfigError("server_error", resp.reason)

    data = await resp.json()
    _LOGGER.debug("(get_api_sensor_config) sensor response: %s", data)

    if not resp.ok:
        if resp.status == HTTPStatus.NOT_FOUND:
            raise PurpleAirApiConfigError("pa_sensor_id", "not_found")

        if resp.status == HTTPStatus.BAD_REQUEST:
            if data.get("error") == "InvalidDataReadKeyError":
                raise PurpleAirApiConfigError("pa_sensor_id", "bad_read_key")

            _LOGGER.error(
                "Bad request error from PurpleAirApi during configuration: %s", data
            )
            raise PurpleAirApiConfigError("bad_request", data.get("description"))

    return data.get("sensor")


def _clean_expired_cache_entries(pa_sensor: SensorReading, epa_avg: deque[EpaAvgValue]):
    """Clean out any old cache entries older than an hour."""
    hour_ago = datetime.utcnow() - timedelta(seconds=3600)
    expired_count = sum(1 for v in epa_avg if v.timestamp < hour_ago)
    if expired_count:
        _LOGGER.info(
            'PuprleAir Sensor "%s" EPA readings contained %s old entries in cache',
            pa_sensor.pa_sensor_id,
            expired_count,
        )
        for _ in range(expired_count):
            epa_avg.popleft()

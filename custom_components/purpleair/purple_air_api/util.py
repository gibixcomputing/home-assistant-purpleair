"""Provides utility functions for the PurpleAir API."""
from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
import logging
from math import fsum
from typing import Any

from .const import (
    API_ATTR_PM25,
    API_ATTR_PM25_AQI,
    API_ATTR_PM25_AQI_RAW,
    AQI_BREAKPOINTS,
    JSON_PROPERTIES,
    MAX_PM_READING,
    PM_PROPERTIES,
)
from .model import (
    EpaAvgValue,
    EpaAvgValueCache,
    PurpleAirApiSensorData,
    PurpleAirApiSensorDataDict,
    PurpleAirApiSensorReading,
)

_LOGGER = logging.getLogger(__name__)

WARNED_SENSORS: list[str] = []


def add_aqi_calculations(
    pa_sensors: PurpleAirApiSensorDataDict, *, cache: EpaAvgValueCache | None = None
) -> None:
    """
    Add AQI calculations as custom properties to the readings.

    This computes the AQI values by calculating them based off the corrections
    and breakpoints, providing a few variations depending what is available.
    """

    if not cache:
        cache = getattr(add_aqi_calculations, "cache", None)
        if not cache:
            _LOGGER.debug("using global cache for EPA values")
            cache = create_epa_value_cache()
            setattr(add_aqi_calculations, "cache", cache)

    for pa_sensor in pa_sensors.values():
        readings = pa_sensor.readings

        confidence = readings.get_confidence(API_ATTR_PM25)
        if pm25atm := readings.pm2_5_atm:
            readings.set_value(
                API_ATTR_PM25_AQI_RAW, calc_aqi(pm25atm, "pm2_5"), confidence
            )

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
        if readings.pm2_5_cf_1 is not None and readings.humidity is not None:
            epa_avg = cache[pa_sensor.pa_sensor_id]
            epa_avg.append(EpaAvgValue(hum=readings.humidity, pm25=readings.pm2_5_cf_1))

            _clean_expired_cache_entries(pa_sensor, epa_avg)

            humidity_avg = round(fsum(v.hum for v in epa_avg) / len(epa_avg), 5)
            pm25cf1_avg = round(fsum(v.pm25 for v in epa_avg) / len(epa_avg), 5)

            pm25_corrected = round(
                (0.534 * pm25cf1_avg) - (0.0844 * humidity_avg) + 5.604, 1
            )
            pm25_corrected_aqi = calc_aqi(pm25_corrected, "pm2_5")

            _LOGGER.debug(
                "(%s): EPA correction: (pm25: %s, hum: %s, corrected: %s, aqi: %s)",
                pa_sensor.pa_sensor_id,
                pm25cf1_avg,
                humidity_avg,
                pm25_corrected,
                pm25_corrected_aqi,
            )

            aqi_status = "stable"
            count = len(epa_avg)
            if count < 12:
                aqi_status = f"calculating ({(12 - count) * 5} mins left)"

            readings.set_value(API_ATTR_PM25_AQI, pm25_corrected_aqi, confidence)
            readings.set_status(API_ATTR_PM25_AQI, aqi_status)


def apply_corrections(readings: PurpleAirApiSensorReading) -> None:
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

    if temperature := readings.temp_f:
        readings.temp_f = temperature - 8
        _LOGGER.debug(
            "applied temperature correction from %s to %s", temperature, readings.temp_f
        )

    if humidity := readings.humidity:
        readings.humidity = humidity + 4
        _LOGGER.debug(
            "applied humidity correction from %s to %s", humidity, readings.humidity
        )


def build_sensors(results: list[dict[str, Any]]) -> dict[str, PurpleAirApiSensorData]:
    """
    Build a dictionary of PurpleAir sensors.

    The data is extracted from available data from the JSON result array returned
    from the PurpleAir API.
    """

    sensors: dict[str, PurpleAirApiSensorData] = {}
    for result in results:
        pa_sensor_id = str(result.get("ParentID", result["ID"]))

        if pa_sensor_id not in sensors:
            sensors[pa_sensor_id] = PurpleAirApiSensorData(
                pa_sensor_id=pa_sensor_id,
                label=str(result.get("Label")),
                last_seen=datetime.fromtimestamp(result["LastSeen"], timezone.utc),
                last_update=datetime.fromtimestamp(
                    result["LastUpdateCheck"], timezone.utc
                ),
                device_location=str(result.get("DEVICE_LOCATIONTYPE", "unknown")),
                version=str(result.get("Version", "unknown")),
                type=str(result.get("Type", "unknown")),
                lat=float(result.get("Lat", 0)) or None,
                lon=float(result.get("Lon", 0)) or None,
                rssi=float(result.get("RSSI", 0)),
                adc=float(result.get("Adc", 0)),
                uptime=int(result.get("Uptime", 0)),
            )

        sensor = sensors[pa_sensor_id]
        readings = sensor.readings

        channel = "B" if "ParentID" in result else "A"
        channel_data = readings.get_channel(channel)
        for prop in JSON_PROPERTIES:
            channel_data[prop] = result.get(prop)  # type: ignore[assignment]

    return sensors


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


def calculate_sensor_values(sensors: dict[str, PurpleAirApiSensorData]) -> None:
    """
    Calculate sensor values by mutating the provided sensor dictionary.

    This iterates over the raw sensor data and provides a normalized view and adds
    any calculated properties.
    """

    for sensor in sensors.values():
        readings: PurpleAirApiSensorReading = sensor.readings
        _LOGGER.debug(
            "(%s): processing data: %s", sensor.pa_sensor_id, readings.channels
        )

        channel_a = readings.get_channel("A")
        if readings.both_channels_have_data():
            channel_b = readings.get_channel("B")
            for prop in JSON_PROPERTIES:
                if a_value := channel_a.get(prop):
                    a_value = float(a_value)

                    if b_value := channel_b.get(prop):
                        b_value = float(b_value)

                        (value, confidence) = get_pm_reading(
                            sensor, prop, a_value, b_value
                        )
                        readings.set_value(prop, value, confidence)
                    else:
                        readings.set_value(prop, round(a_value, 1), "single")
                else:
                    readings.set_value(prop, None)
        else:
            for prop in JSON_PROPERTIES:
                if a_value := channel_a.get(prop):
                    a_value = float(a_value)
                    readings.set_value(prop, round(a_value, 1), "good")
                else:
                    readings.set_value(prop, None)

        apply_corrections(readings)

        # clean up intermediate results
        readings.clear_temporary_data()


def clear_sensor_warning(pa_sensor: PurpleAirApiSensorData) -> None:
    """Remove a sensor from the warned sensor list."""
    if pa_sensor.pa_sensor_id in WARNED_SENSORS:
        WARNED_SENSORS.remove(pa_sensor.pa_sensor_id)


def create_epa_value_cache() -> EpaAvgValueCache:
    """Create a new, empty EPA value cache."""
    cache: EpaAvgValueCache = defaultdict(lambda: deque(maxlen=12))
    return cache


def get_pm_reading(
    pa_sensor: PurpleAirApiSensorData, prop: str, a_value: float, b_value: float
) -> tuple[float | None, str]:
    """Get a value and confidence level for the given PM reading."""

    a_valid = a_value < MAX_PM_READING
    b_valid = b_value < MAX_PM_READING
    diff = abs(a_value - b_value)
    value = None

    # shouldn't get here as non PM-props are only on channel A
    if prop not in PM_PROPERTIES:
        value = round((a_value + b_value) / 2, 1)
        confidence = "good"
        clear_sensor_warning(pa_sensor)
    elif a_valid and b_valid:
        value = round((a_value + b_value) / 2, 1)
        confidence = "good" if diff < 45 else "questionable"
        clear_sensor_warning(pa_sensor)
    elif a_valid and not b_valid:
        value = round(a_value, 1)
        confidence = "single - b channel bad"
        warn_sensor_channel_bad(pa_sensor, prop, "B")
    elif not a_valid and b_valid:
        value = round(b_value, 1)
        confidence = "single - a channel bad"
        warn_sensor_channel_bad(pa_sensor, prop, "A")
    else:
        value = None
        confidence = "invalid"
        warn_sensor_channel_bad(pa_sensor, prop, "A and B")

    return (value, confidence)


def warn_sensor_channel_bad(
    pa_sensor: PurpleAirApiSensorData, prop: str, channel: str
) -> None:
    """
    Log a warning if a sensor is returning bad data for a collector channel.

    Only logs if the sensor has not already logged a warning.
    """
    if pa_sensor.pa_sensor_id in WARNED_SENSORS:
        return

    WARNED_SENSORS.append(pa_sensor.pa_sensor_id)
    _LOGGER.warning(
        'PurpleAir Sensor "%s" (%s) is sending bad readings for channel %s data point %s',
        pa_sensor.label,
        pa_sensor.pa_sensor_id,
        channel,
        prop,
    )


def _clean_expired_cache_entries(
    pa_sensor: PurpleAirApiSensorData, epa_avg: deque[EpaAvgValue]
) -> None:
    """Clean out any old cache entries older than an hour."""
    hour_ago = datetime.utcnow() - timedelta(seconds=3600)
    expired_count = sum(1 for v in epa_avg if v.timestamp < hour_ago)
    if expired_count:
        _LOGGER.info(
            'PuprleAir Sensor "%s" (%s) EPA readings contained %s old entries in cache',
            pa_sensor.label,
            pa_sensor.pa_sensor_id,
            expired_count,
        )
        for _ in range(expired_count):
            epa_avg.popleft()

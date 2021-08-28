"""Provides utility functions for the PurpleAir API."""
import logging
from datetime import datetime, timezone

from .const import (
    AQI_BREAKPOINTS,
    API_ATTR_PM25,
    API_ATTR_PM25_AQI,
    API_ATTR_PM25_AQI_RAW,
    API_ATTR_PM25_CF1,
    API_ATTR_HUMIDITY,
    API_ATTR_TEMP_F,
    JSON_PROPERTIES,
    MAX_PM_READING,
    PM_PROPERTIES,
)

_LOGGER = logging.getLogger(__name__)

WARNED_NODES = []

EPA_AVG_DATA = {}


def add_aqi_calculations(node, readings):
    """
    This adds the custom AQI properties to the readings, calculating them based off the corrections
    and breakpoints, providing a few variations depending what is needed.
    """

    confidence = readings.get(f'{API_ATTR_PM25}_confidence')
    if pm25atm := readings.get(API_ATTR_PM25):
        readings[API_ATTR_PM25_AQI_RAW] = calc_aqi(pm25atm, 'pm2_5')
        readings[f'{API_ATTR_PM25_AQI_RAW}_confidence'] = confidence

    # get the pm2.5 CF=1 reading. This should already be averaged between A and B if healthy, or a
    # single sensor if unhealthy.
    pm25cf1 = readings.get(API_ATTR_PM25_CF1)
    humidity = readings.get(API_ATTR_HUMIDITY)
    epa_avg = EPA_AVG_DATA.get(node)

    if not epa_avg:
        epa_avg = {'hum': [], 'pm25': []}
        EPA_AVG_DATA[node] = epa_avg

    # if we have the PM2.5 CF=1 and humidity data, we can calculate AQI using the EPA corrections
    # that were identified to better calibrate PurpleAir sensors to the EPA NowCast AQI formula.
    # This was identified during the 2020 wildfire season and better represents AQI with wildfire
    # smoke for the unhealthy for sensitive groups/unhealthy for everyone AQI breakpoints. Unlike
    # the raw AQI sensor, this is averaged over the last hour. For simplicity, this is applied here
    # as a rolling hour average and provides instant results as readings are provided. No attempt is
    # made to handle missed readings and assumes readings are updated every 5 minutes.
    #
    # The formula is identified as:
    #   PM2.5 corrected= 0.534*[PA_cf1(avgAB)] - 0.0844*RH +5.604
    if pm25cf1 and humidity:
        epa_avg['hum'].append(humidity)
        epa_avg['pm25'].append(pm25cf1)

        # prune the lists to the last 12 entries (1 reading every 5 minutes = 12 per hour)
        while len(epa_avg['hum']) > 12:
            epa_avg['hum'].pop(0)

        while len(epa_avg['pm25']) > 12:
            epa_avg['pm25'].pop(0)

        humidity_avg = sum(epa_avg['hum']) / len(epa_avg['hum'])
        pm25cf1_avg = sum(epa_avg['pm25']) / len(epa_avg['pm25'])

        pm25_corrected = (0.534 * pm25cf1_avg) - (0.0844 * humidity_avg) + 5.604
        pm25_corrected_aqi = calc_aqi(pm25_corrected, 'pm2_5')

        _LOGGER.debug(
            '(%s): EPA correction: (pm25: %s, hum: %s, corrected: %s, aqi: %s)',
            node, pm25cf1_avg, humidity_avg, pm25_corrected, pm25_corrected_aqi
        )

        readings[API_ATTR_PM25_AQI] = pm25_corrected_aqi
        aqi_status = 'ready'

        count = len(epa_avg['pm25'])
        if count < 12:
            aqi_status = f'initializing ({(12 - count) * 5} mins left)'

        readings[f'{API_ATTR_PM25_AQI}_confidence'] = confidence
        readings[f'{API_ATTR_PM25_AQI}_aqi_status'] = aqi_status


def apply_corrections(readings):
    """
    The sensors for temperature and humidity are known to be slightly outside of real values, this
    will apply a blanket correction of subtracting 8°F from the temperature and adding 4% to the
    humidity value. This is documented as the average variance for those two sensor values.

    From the docs:
        Humidity:
            Relative humidity inside of the sensor housing (%). On average, this is 4% lower than
            ambient conditions. Null if not equipped.

        Temperature:
            Temperature inside of the sensor housing (F). On average, this is 8F higher than ambient
            conditions. Null if not equipped.
    """

    if temperature := readings.get(API_ATTR_TEMP_F):
        readings[API_ATTR_TEMP_F] = temperature - 8
        _LOGGER.debug('applied temperature correction from %s to %s',
                      temperature, readings[API_ATTR_TEMP_F])

    if humidity := readings.get(API_ATTR_HUMIDITY):
        readings[API_ATTR_HUMIDITY] = humidity + 4
        _LOGGER.debug('applied humidity correction from %s to %s',
                      humidity, readings[API_ATTR_HUMIDITY])


def build_nodes(results):
    """
    Builds a dictionary of nodes and extracts available data from the JSON result array returned
    from the PurpleAir API.
    """

    nodes = {}
    for result in results:
        sensor = 'A' if 'ParentID' not in result else 'B'
        node_id = str(result['ID'])

        if sensor == 'A':
            nodes[node_id] = {
                'last_seen': datetime.fromtimestamp(result['LastSeen'], timezone.utc),
                'last_update': datetime.fromtimestamp(result['LastUpdateCheck'], timezone.utc),
                'device_location': result.get('DEVICE_LOCATIONTYPE', 'unknown'),
                'readings': {},
                'version': result.get('Version', 'unknown'),
                'type': result.get('Type', 'unknown'),
                'label': result.get('Label'),
                'lat': float(result.get('Lat', 0)),
                'lon': float(result.get('Lon', 0)),
                'rssi': float(result.get('RSSI', 0)),
                'adc': float(result.get('Adc', 0)),
                'uptime': int(result.get('Uptime', 0)),
            }
        else:
            node_id = str(result['ParentID'])

        readings = nodes[node_id]['readings']

        sensor_data = readings.get(sensor, {})
        for prop in JSON_PROPERTIES:
            sensor_data[prop] = result.get(prop)

        if not all(value is None for value in sensor_data.values()):
            readings[sensor] = sensor_data
        else:
            _LOGGER.debug('node %s:%s did not contain any data', node_id, sensor)

    return nodes


def calc_aqi(value, index):
    """
    Calculates the corresponding air quality index based off the available conversion data using
    the sensors current Particulate Matter 2.5 value.

    Returns an AQI between 0 and 999 or None if the sensor reading is invalid.

    See AQI_BREAKPOINTS in const.py.
    """

    if index not in AQI_BREAKPOINTS:
        _LOGGER.debug('calc_aqi requested for unknown type: %s', index)
        return None

    aqi_bp_index = AQI_BREAKPOINTS[index]
    aqi_bp = next((bp for bp in aqi_bp_index if bp.pm_low <= value <= bp.pm_high), None)

    if not aqi_bp:
        _LOGGER.debug('value %s did not fall in valid range for type %s', value, index)
        return None

    aqi_range = aqi_bp.aqi_high - aqi_bp.aqi_low
    pm_range = aqi_bp.pm_high - aqi_bp.pm_low
    aqi_c = value - aqi_bp.pm_low
    return round((aqi_range / pm_range) * aqi_c + aqi_bp.aqi_low)


def calculate_sensor_values(nodes):
    """
    Mutates the provided node dictionary in place by iterating over the raw sensor data and provides
    a normalized view and adds any calculated properties.
    """

    for node in nodes:
        readings = nodes[node]['readings']
        _LOGGER.debug('(%s): processing readings: %s', node, readings)

        if 'A' in readings and 'B' in readings:
            for prop in JSON_PROPERTIES:
                if a_value := readings['A'].get(prop):
                    a_value = float(a_value)

                    if b_value := readings['B'].get(prop):
                        b_value = float(b_value)

                        label = nodes[node]['label']

                        (value, confidence) = get_pm_reading(node, prop, a_value, b_value, label)

                        readings[prop] = value
                        readings[f'{prop}_confidence'] = confidence
                    else:
                        readings[prop] = round(a_value, 1)
                        readings[f'{prop}_confidence'] = 'single'
                else:
                    readings[prop] = None
        else:
            for prop in JSON_PROPERTIES:
                if prop in readings['A']:
                    a_value = float(readings['A'][prop])
                    readings[prop] = round(a_value, 1)
                    readings[f'{prop}_confidence'] = 'good'
                else:
                    readings[prop] = None

        apply_corrections(readings)
        add_aqi_calculations(node, readings)

        # clean up intermediate results
        readings.pop('A', None)
        readings.pop('B', None)

        _LOGGER.debug('(%s): results: %s', node, readings)


def get_pm_reading(node: str, prop: str, a_value: float, b_value: float, label: str):
    """Gets a value and confidence level for the given PM reading."""

    a_valid = a_value < MAX_PM_READING
    b_valid = b_value < MAX_PM_READING
    diff = abs(a_value - b_value)
    value = None

    # shouldn't get here as non PM-props are only on channel A
    if prop not in PM_PROPERTIES:
        value = round((a_value + b_value) / 2, 1)
        confidence = 'good'
        clear_node_warning(node)
    elif a_valid and b_valid:
        value = round((a_value + b_value) / 2, 1)
        confidence = 'good' if diff < 45 else 'questionable'
        clear_node_warning(node)
    elif a_valid and not b_valid:
        value = round(a_value, 1)
        confidence = 'single - b channel bad'
        warn_node_channel_bad(node, label, prop, 'B')
    elif not a_valid and b_valid:
        value = round(b_value, 1)
        confidence = 'single - a channel bad'
        warn_node_channel_bad(node, label, prop, 'A')
    else:
        value = None
        confidence = 'invalid'
        warn_node_channel_bad(node, label, prop, 'A and B')

    return (value, confidence)


def clear_node_warning(node: str):
    """Removes a node from the warning node list."""
    if node in WARNED_NODES:
        WARNED_NODES.remove(node)


def warn_node_channel_bad(node: str, label: str, prop: str, channel: str):
    """
    Logs a warning if a node is returning bad data for a sensor channel, if the node has not already
    logged a warning.
    """
    if node in WARNED_NODES:
        return

    WARNED_NODES.append(node)
    _LOGGER.warning(
        'PurpleAir Sensor "%s" (%s) is sending bad readings for channel %s data point %s',
        label, node, channel, prop
    )

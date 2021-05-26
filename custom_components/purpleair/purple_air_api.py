"""
Provides an API capable of communicating with the free PurpleAir service.
"""

from datetime import timedelta
import logging

from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval, async_track_point_in_utc_time
from homeassistant.util import dt

from .const import (
    AQI_BREAKPOINTS, DISPATCHER_PURPLE_AIR,
    JSON_PROPERTIES, SCAN_INTERVAL,
    PUBLIC_URL, PRIVATE_URL
)

_LOGGER = logging.getLogger(__name__)


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
    aqi_bp = next((bp for bp in aqi_bp_index if bp['pm_low'] <= value <= bp['pm_high']), None)

    if not aqi_bp:
        _LOGGER.debug('value %s did not fall in valid range for type %s', value, index)
        return None

    aqi_range = aqi_bp['aqi_high'] - aqi_bp['aqi_low']
    pm_range = aqi_bp['pm_high'] - aqi_bp['pm_low']
    aqi_c = value - aqi_bp['pm_low']
    return round((aqi_range / pm_range) * aqi_c + aqi_bp['aqi_low'])


class PurpleAirApi:
    """Provides the API capable of communicating with PurpleAir."""

    def __init__(self, hass, session):
        self._hass = hass
        self._session = session
        self._nodes = {}
        self._data = {}
        self._scan_interval = timedelta(seconds=SCAN_INTERVAL)
        self._shutdown_interval = None

    def is_node_registered(self, node_id):
        """
        Returns a value indicating whether the provided node is already registered with this
        instance.
        """
        return node_id in self._data

    def get_property(self, node_id, prop):
        """Gets the property value of a sensor based on the node id."""

        if node_id not in self._data:
            return None

        node = self._data[node_id]
        return node[prop]

    def get_reading(self, node_id, prop):
        """Gets the last recorded reading of a sensor based on the node id."""

        readings = self.get_property(node_id, 'readings')
        return readings[prop] if prop in readings else None

    def register_node(self, node_id, hidden, key):
        """
        Registers a node with this instance. This will schedule a periodic poll against PurpleAir if
        this is the first sensor added and schedule an immediate API request after 5 seconds.
        """

        if node_id in self._nodes:
            _LOGGER.debug('detected duplicate registration: %s', node_id)
            return

        self._nodes[node_id] = {'hidden': hidden, 'key': key}
        _LOGGER.debug('registered new node: %s', node_id)

        if not self._shutdown_interval:
            _LOGGER.debug('starting background poll: %s', self._scan_interval)
            self._shutdown_interval = async_track_time_interval(
                self._hass,
                self._update,
                self._scan_interval
            )

            async_track_point_in_utc_time(
                self._hass,
                self._update,
                dt.utcnow() + timedelta(seconds=5)
            )

    def unregister_node(self, node_id):
        """
        Unregisters a node from this instance and removes any associated data. If this is the last
        registered node the periodic polling is shut down.
        """

        if node_id not in self._nodes:
            _LOGGER.debug('detected non-existent unregistration: %s', node_id)
            return

        del self._nodes[node_id]
        _LOGGER.debug('unregistered node: %s', node_id)

        if not self._nodes and self._shutdown_interval:
            _LOGGER.debug('no more nodes, shutting down interval')
            self._shutdown_interval()
            self._shutdown_interval = None

    def _build_api_urls(self, public_nodes, private_nodes):
        """
        Builds a list of URLs to query based off the provided public and private node lists,
        attempting to combine as many sensors in to as few API requests as possible.
        """

        urls = []
        if private_nodes:
            by_keys = {}
            for node in private_nodes:
                data = self._nodes[node]
                key = data['key'] if 'key' in data else None

                if key:
                    if key not in by_keys:
                        by_keys[key] = []

                    by_keys[key].append(node)

            used_public = False
            for key, private_nodes_for_key in by_keys.items():
                nodes = private_nodes_for_key
                if not used_public:
                    nodes += public_nodes
                    used_public = True

                urls.append(PRIVATE_URL.format(nodes='|'.join(nodes), key=key))

        elif public_nodes:
            urls = [PUBLIC_URL.format(nodes='|'.join(public_nodes))]

        return urls

    async def _fetch_data(self, urls):
        """Fetches data from the PurpleAir API endpoint."""

        if not urls:
            _LOGGER.debug('no nodes provided')
            return []

        results = []
        for url in urls:
            _LOGGER.debug('fetching url: %s', url)

            async with self._session.get(url) as response:
                if response.status != 200:
                    _LOGGER.warning('bad API response for %s: %s', url, response.status)

                json = await response.json()
                results += json['results']

        return results

    async def _update(self, now=None):
        """Main update process to query and update sensor data."""

        public_nodes = [node_id for node_id in self._nodes if not self._nodes[node_id]['hidden']]
        private_nodes = [node_id for node_id in self._nodes if self._nodes[node_id]['hidden']]

        _LOGGER.debug('public nodes: %s, private nodes: %s', public_nodes, private_nodes)

        urls = self._build_api_urls(public_nodes, private_nodes)
        results = await self._fetch_data(urls)

        nodes = build_nodes(results)

        calculate_sensor_values(nodes)

        self._data = nodes
        async_dispatcher_send(self._hass, DISPATCHER_PURPLE_AIR)


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
                'last_seen': result['LastSeen'],
                'last_update': result['LastUpdateCheck'],
                'device_location':
                result['DEVICE_LOCATIONTYPE'] if 'DEVICE_LOCATIONTYPE'
                in result else 'unknown',
                'readings': {},
            }
        else:
            node_id = str(result['ParentID'])

        readings = nodes[node_id]['readings']

        sensor_data = readings[sensor] if sensor in readings else {}
        for prop in JSON_PROPERTIES:
            sensor_data[prop] = result[prop] if prop in result else None

        if not all(value is None for value in sensor_data.values()):
            readings[sensor] = sensor_data
        else:
            _LOGGER.debug('node %s:%s did not contain any data', node_id, sensor)

    return nodes


def calculate_sensor_values(nodes):
    """
    Mutates the provided ndoe dictionary in place by iterating over the raw sensor data and provides
    a normalized view and adds any calculated properties.
    """

    for node in nodes:
        readings = nodes[node]['readings']
        _LOGGER.debug('processing node %s, readings: %s', node, readings)

        if 'A' in readings and 'B' in readings:
            for prop in JSON_PROPERTIES:
                if prop in readings['A'] and prop in readings['B']:
                    a_reading = float(readings['A'][prop])
                    b_reading = float(readings['B'][prop])
                    readings[prop] = round((a_reading + b_reading) / 2, 1)

                    confidence = 'Good' if abs(a_reading - b_reading) < 45 else 'Questionable'
                    readings[f'{prop}_confidence'] = confidence
                else:
                    readings[prop] = None
        else:
            for prop in JSON_PROPERTIES:
                if prop in readings['A']:
                    a_reading = float(readings['A'][prop])
                    readings[prop] = round(a_reading, 1)
                    readings[f'{prop}_confidence'] = 'Good'
                else:
                    readings[prop] = None

        _LOGGER.debug('node results %s, readings: %s', node, readings)

        if 'pm2_5_atm' in readings and readings['pm2_5_atm']:
            readings['pm2_5_atm_aqi'] = calc_aqi(readings['pm2_5_atm'], 'pm2_5')

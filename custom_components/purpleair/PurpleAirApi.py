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
    if index not in AQI_BREAKPOINTS:
        _LOGGER.debug('calc_aqi requested for unknown type: %s', index)
        return None

    bp = next((bp for bp in AQI_BREAKPOINTS[index] if value >= bp['pm_low'] and value
              <= bp['pm_high']), None)
    if not bp:
        _LOGGER.debug('value %s did not fall in valid range for type %s', value, index)
        return None

    aqi_range = bp['aqi_high'] - bp['aqi_low']
    pm_range = bp['pm_high'] - bp['pm_low']
    c = value - bp['pm_low']
    return round((aqi_range / pm_range) * c + bp['aqi_low'])


class PurpleAirApi:
    def __init__(self, hass, session):
        self._hass = hass
        self._session = session
        self._nodes = {}
        self._data = {}
        self._scan_interval = timedelta(seconds=SCAN_INTERVAL)
        self._shutdown_interval = None

    def is_node_registered(self, node_id):
        return node_id in self._data

    def get_property(self, node_id, prop):
        if node_id not in self._data:
            return None

        node = self._data[node_id]
        return node[prop]

    def get_reading(self, node_id, prop):
        readings = self.get_property(node_id, 'readings')
        return readings[prop] if prop in readings else None

    def register_node(self, node_id, hidden, key):
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
        if node_id not in self._nodes:
            _LOGGER.debug('detected non-existent unregistration: %s', node_id)
            return

        del self._nodes[node_id]
        _LOGGER.debug('unregistered node: %s', node_id)

        if not self._nodes and self._shutdown_interval:
            _LOGGER.debug('no more nodes, shutting down interval')
            self._shutdown_interval()
            self._shutdown_interval = None

    def _build_private_urls(self, public_nodes, private_nodes):
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

    async def _fetch_data(self, public_nodes, private_nodes):
        urls = self._build_private_urls(public_nodes, private_nodes)

        if not urls:
            _LOGGER.debug('no nodes provided')
            return []

        _LOGGER.debug('fetch url list: %s', urls)

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
        public_nodes = [node_id for node_id in self._nodes if not self._nodes[node_id]['hidden']]
        private_nodes = [node_id for node_id in self._nodes if self._nodes[node_id]['hidden']]

        _LOGGER.debug('public nodes: %s, private nodes: %s', public_nodes, private_nodes)

        results = await self._fetch_data(public_nodes, private_nodes)

        nodes = build_nodes(results)

        for node in nodes:
            readings = nodes[node]['readings']
            _LOGGER.debug('processing node %s, readings: %s', node, readings)

            if 'A' in readings and 'B' in readings:
                for prop in JSON_PROPERTIES:
                    if prop in readings['A'] and prop in readings['B']:
                        a = float(readings['A'][prop])
                        b = float(readings['B'][prop])
                        readings[prop] = round((a + b) / 2, 1)

                        confidence = 'Good' if abs(a - b) < 45 else 'Questionable'
                        readings[f'{prop}_confidence'] = confidence
                    else:
                        readings[prop] = None
            else:
                for prop in JSON_PROPERTIES:
                    if prop in readings['A']:
                        a = float(readings['A'][prop])
                        readings[prop] = round(a, 1)
                        readings[f'{prop}_confidence'] = 'Good'
                    else:
                        readings[prop] = None

            _LOGGER.debug('node results %s, readings: %s', node, readings)

            if 'pm2_5_atm' in readings and readings['pm2_5_atm']:
                readings['pm2_5_atm_aqi'] = calc_aqi(readings['pm2_5_atm'], 'pm2_5')

        self._data = nodes
        async_dispatcher_send(self._hass, DISPATCHER_PURPLE_AIR)


def build_nodes(results):
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

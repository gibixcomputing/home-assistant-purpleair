"""
Provides an API capable of communicating with the free PurpleAir service.
"""

import asyncio
import logging
import re
from typing import Dict, List

from aiohttp import ClientSession

from .const import PRIVATE_URL, PUBLIC_URL
from .exceptions import (
    PurpleAirApiError,
    PurpleAirApiStatusError,
    PurpleAirApiUrlError,
)
from .model import (
    EpaAvgValueCache,
    PurpleAirApiConfigEntry,
)
from .util import (
    add_aqi_calculations,
    build_nodes,
    calculate_sensor_values,
    create_epa_value_cache,
)

_LOGGER = logging.getLogger(__name__)


class PurpleAirApi:
    """Provides the API capable of communicating with PurpleAir."""

    nodes: Dict[str, PurpleAirApiConfigEntry]
    session: ClientSession
    _api_issues: bool
    _cache: EpaAvgValueCache

    def __init__(self, session: ClientSession):
        self.nodes = {}
        self.session = session

        self._api_issues = False
        self._cache = create_epa_value_cache()

    def get_node_count(self):
        """Gets the number of nodes registered with the API."""
        return len(self.nodes)

    def register_node(self, node: PurpleAirApiConfigEntry):
        """
        Registers a node with this instance. This will schedule a periodic poll against PurpleAir if
        this is the first sensor added and schedule an immediate API request after 5 seconds.
        """

        if node.node_id in self.nodes:
            _LOGGER.debug('detected duplicate registration: %s', node.node_id)
            return

        self.nodes[node.node_id] = PurpleAirApiConfigEntry(
            node_id=node.node_id,
            title=node.title,
            key=node.key,
            hidden=node.hidden
        )
        _LOGGER.debug('registered new node: %s', node.node_id)

    def unregister_node(self, node_id):
        """
        Unregisters a node from this instance and removes any associated data. If this is the last
        registered node the periodic polling is shut down.
        """

        if node_id not in self.nodes:
            _LOGGER.debug('detected non-existent unregistration: %s', node_id)
            return

        del self.nodes[node_id]
        _LOGGER.debug('unregistered node: %s', node_id)

    async def update(self):
        """Main update process to query and update sensor data."""

        public_nodes = [node_id for (node_id, data) in self.nodes.items() if not data.hidden]
        private_nodes = [node_id for (node_id, data) in self.nodes.items() if data.hidden]

        _LOGGER.debug('public nodes: %s, private nodes: %s', public_nodes, private_nodes)

        urls = self._build_api_urls(public_nodes, private_nodes)
        results = await self._fetch_data(urls)

        nodes = build_nodes(results)

        calculate_sensor_values(nodes)
        add_aqi_calculations(nodes, cache=self._cache)

        for (node_id, node) in nodes.items():
            _LOGGER.debug('(%s): results: %s', node_id, node)

        return nodes

    def _build_api_urls(self, public_nodes, private_nodes):
        """
        Builds a list of URLs to query based off the provided public and private node lists,
        attempting to combine as many sensors in to as few API requests as possible.
        """

        urls: List[str] = []
        if private_nodes:
            by_keys: Dict[str, str] = {}
            for node_id in private_nodes:
                node = self.nodes[node_id]
                key = node.key

                if key:
                    if key not in by_keys:
                        by_keys[key] = []

                    by_keys[key].append(node_id)

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

            # be nice to the free API when fetching multiple URLs
            await asyncio.sleep(0.5)

            async with self.session.get(url) as response:
                if response.status != 200:
                    if not self._api_issues:
                        self._api_issues = True
                        _LOGGER.warning(
                            'PurpleAir API returned bad response (%s) for url %s. %s',
                            response.status,
                            url,
                            await response.text()
                        )

                    continue

                if self._api_issues:
                    self._api_issues = False
                    _LOGGER.info('PurpleAir API responding normally')

                json = await response.json()
                results += json['results']

        return results


async def get_node_configuration(session: ClientSession, url: str):
    """
    Gets a configuration for the node at the  given PurpleAir URL. This string expects to see a URL
    in the following format:

        https://www.purpleair.com/json?key={key}&show={node_id}
        https://www.purpleair.com/sensorlist?key={key}&show={node_id}
    """

    if not re.match(r'.*purpleair.*', url, re.IGNORECASE):
        raise PurpleAirApiUrlError('Provided URL is invalid', url)

    key_match = re.match(r'.*key=(?P<key>[^&]+)', url)
    node_match = re.match(r'.*show=(?P<node_id>[^&]+)', url)

    key = key_match.group('key') if key_match else None
    node_id = node_match.group('node_id') if node_match else None

    if not key or not node_id:
        raise PurpleAirApiUrlError('Unable to get node and/or key from URL', url)

    api_url = PRIVATE_URL.format(nodes=node_id, key=key)
    _LOGGER.debug('getting node info from url %s', api_url)

    data = {}
    async with session.get(api_url) as response:
        if not response.status == 200:
            raise PurpleAirApiStatusError(api_url, response.status, await response.text())

        data = await response.json()

    results = data.get('results', [])
    if not results or len(results) == 0:
        raise PurpleAirApiError('Missing results from JSON response')

    node = results[0]
    _LOGGER.debug('got node %s', node)
    node_id = node.get('ParentID') or node['ID']
    if not node_id:
        raise PurpleAirApiError('Missing node ID or ParentID')

    node_id = str(node_id)

    config = PurpleAirApiConfigEntry(
        node_id=node_id,
        title=node.get('Label'),
        hidden=node.get('Hidden') == 'true',
        key=node.get('THINGSPEAK_PRIMARY_ID_READ_KEY')
    )

    _LOGGER.debug('generated config for node %s: %s', node_id, config)

    return config

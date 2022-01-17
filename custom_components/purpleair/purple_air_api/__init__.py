"""Provides an API capable of communicating with the free PurpleAir service. """
from __future__ import annotations

import asyncio
import logging
from urllib.parse import parse_qs, urlsplit

from aiohttp import ClientSession

from .const import PRIVATE_URL, PUBLIC_URL
from .exceptions import (
    PurpleAirApiInvalidResponseError,
    PurpleAirApiStatusError,
    PurpleAirApiUrlError,
)
from .model import EpaAvgValueCache, PurpleAirApiConfigEntry
from .util import (
    add_aqi_calculations,
    build_sensors,
    calculate_sensor_values,
    create_epa_value_cache,
)

_LOGGER = logging.getLogger(__name__)


class PurpleAirApi:
    """Provides the API capable of communicating with PurpleAir."""

    sensors: dict[str, PurpleAirApiConfigEntry]
    session: ClientSession
    _api_issues: bool
    _cache: EpaAvgValueCache

    def __init__(self, session: ClientSession):
        self.sensors = {}
        self.session = session

        self._api_issues = False
        self._cache = create_epa_value_cache()

    def get_sensor_count(self):
        """Gets the number of sensors registered with the API."""
        return len(self.sensors)

    def register_sensor(
        self, pa_sensor_id: str, title: str, hidden: bool, key: str | None = None
    ):
        """
        Registers a sensor with this instance. This will schedule a periodic poll against PurpleAir
        if this is the first sensor added and schedule an immediate API request after 5 seconds.
        """

        if pa_sensor_id in self.sensors:
            _LOGGER.debug("detected duplicate registration: %s", pa_sensor_id)
            return

        sensor = PurpleAirApiConfigEntry(
            pa_sensor_id=pa_sensor_id, title=title, key=key, hidden=hidden
        )

        self.sensors[pa_sensor_id] = sensor
        _LOGGER.debug("registered new sensor: %s", sensor)

    def unregister_sensor(self, pa_sensor_id: str):
        """Unregisters a sensor from this instance and removes any associated data."""

        if pa_sensor_id not in self.sensors:
            _LOGGER.debug("detected non-existent unregistration: %s", pa_sensor_id)
            return

        del self.sensors[pa_sensor_id]
        _LOGGER.debug("unregistered sensor: %s", pa_sensor_id)

    async def update(self):
        """Main update process to query and update sensor data."""

        public_sensors = [s.pa_sensor_id for s in self.sensors.values() if not s.hidden]
        private_sensors = [s.pa_sensor_id for s in self.sensors.values() if s.hidden]

        _LOGGER.debug(
            "public sensors: %s, private sensors: %s", public_sensors, private_sensors
        )

        urls = self._build_api_urls(public_sensors, private_sensors)
        results = await self._fetch_data(urls)

        sensors = build_sensors(results)

        calculate_sensor_values(sensors)
        add_aqi_calculations(sensors, cache=self._cache)

        if _LOGGER.isEnabledFor(logging.DEBUG):
            for sensor in sensors.values():
                _LOGGER.debug("(%s) sensor data: %s", sensor.pa_sensor_id, sensor)

        return sensors

    def _build_api_urls(self, public_sensors, private_sensors):
        """
        Builds a list of URLs to query based off the provided public and private sensor lists,
        attempting to combine as many sensors in to as few API requests as possible.
        """

        urls: list[str] = []
        if private_sensors:
            by_keys: dict[str, str] = {}
            for pa_sensor_id in private_sensors:
                key = self.sensors[pa_sensor_id].key

                if key:
                    if key not in by_keys:
                        by_keys[key] = []

                    by_keys[key].append(pa_sensor_id)

            used_public = False
            for key, private_sensors_for_key in by_keys.items():
                sensors = private_sensors_for_key
                if not used_public:
                    sensors += public_sensors
                    used_public = True

                urls.append(PRIVATE_URL.format(sensors="|".join(sensors), key=key))

        elif public_sensors:
            urls = [PUBLIC_URL.format(sensors="|".join(public_sensors))]

        return urls

    async def _fetch_data(self, urls):
        """Fetches data from the PurpleAir API endpoint."""

        if not urls:
            _LOGGER.debug("no sensors provided")
            return []

        results = []
        for url in urls:
            _LOGGER.debug("fetching url: %s", url)

            # be nice to the free API when fetching multiple URLs
            await asyncio.sleep(0.5)

            async with self.session.get(url) as response:
                if response.status != 200:
                    if not self._api_issues:
                        self._api_issues = True
                        _LOGGER.warning(
                            "PurpleAir API returned bad response (%s) for url %s. %s",
                            response.status,
                            url,
                            await response.text(),
                        )

                    continue

                if self._api_issues:
                    self._api_issues = False
                    _LOGGER.info("PurpleAir API responding normally")

                json = await response.json()
                results += json["results"]

        return results


async def get_sensor_configuration(
    session: ClientSession, url: str
) -> PurpleAirApiConfigEntry:
    """
    Gets a configuration for the sensor at the given PurpleAir URL. This string expects to see a URL
    in the following format:

        https://www.purpleair.com/json?key={key}&show={pa_sensor_id}
        https://www.purpleair.com/sensorlist?key={key}&show={pa_sensor_id}
    """

    try:
        parsed_url = urlsplit(url)
    except Exception as error:
        raise PurpleAirApiUrlError("Error parsing URL", url) from error

    hostname = parsed_url.hostname or ""
    if "purpleair" not in hostname:
        raise PurpleAirApiUrlError("Unrecognized URL", url)

    query = parse_qs(parsed_url.query)
    key = query.get("key", [""])[0]
    pa_sensor_id = query.get("show", [""])[0]

    if not pa_sensor_id:
        raise PurpleAirApiUrlError("Unable to get sensor id and/or key from URL", url)

    api_url = PRIVATE_URL.format(sensors=pa_sensor_id, key=key)
    _LOGGER.debug("getting sensor info from url %s", api_url)

    data: dict[str, dict] = {}
    async with session.get(api_url) as response:
        if response.status != 200:
            raise PurpleAirApiStatusError(
                api_url, response.status, await response.text()
            )

        data = await response.json()

    results = data.get("results", [])  # type: ignore
    if not results or len(results) == 0:
        raise PurpleAirApiInvalidResponseError(
            "Missing results from JSON response", results
        )

    sensor: dict = results[0]
    _LOGGER.debug("got sensor %s", sensor)
    pa_sensor_id = sensor.get("ParentID") or sensor["ID"]
    if not pa_sensor_id:
        raise PurpleAirApiInvalidResponseError("Missing ID or ParentID", sensor)

    pa_sensor_id = str(pa_sensor_id)

    config = PurpleAirApiConfigEntry(
        pa_sensor_id=pa_sensor_id,
        title=str(sensor.get("Label")),
        hidden=sensor.get("Hidden") == "true",
        key=sensor.get("THINGSPEAK_PRIMARY_ID_READ_KEY"),
    )

    _LOGGER.debug("generated config for sensor %s: %s", pa_sensor_id, config)

    return config

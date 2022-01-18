"""Utility functions for the v1 PurpleAir API."""
from __future__ import annotations

from http import HTTPStatus
import logging

from aiohttp import ClientResponse, ClientSession

from .const import URL_API_V1_KEYS_URL, URL_API_V1_SENSOR
from .exceptions import PurpleAirApiConfigError
from .model import ApiConfigEntry

_LOGGER = logging.getLogger(__name__)


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
    |--------------|--------------|----------------------------------------------|
    | server_error | str          | .extra is the HTTP reason string.            |
    |--------------|--------------|----------------------------------------------|
    | pa_sensor_id | missing      | The parameter is missing.                    |
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
        if not resp.ok:
            raise PurpleAirApiConfigError("api_key", "bad_status")

        key_data = await resp.json()
        if key_data.get("api_key_type") != "READ":
            raise PurpleAirApiConfigError("api_key", "not_read_key")

    config_fields = [
        "name",
        "primary_id_a",
        "primary_key_a",
        "private",
        "sensor_index",
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

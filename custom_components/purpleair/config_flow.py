"""Config flow for Purple Air integration."""
from __future__ import annotations

import logging
from typing import Any, Final

from homeassistant.config_entries import CONN_CLASS_CLOUD_POLL, ConfigFlow
from homeassistant.const import CONF_API_KEY, CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .const import DOMAIN
from .model import PurpleAirConfigEntry
from .purple_air_api.exceptions import (
    PurpleAirApiInvalidResponseError,
    PurpleAirApiStatusError,
    PurpleAirApiUrlError,
)
from .purple_air_api.v1.util import get_api_sensor_config

_LOGGER = logging.getLogger(__name__)

CONF_PA_SENSOR_READ_KEY: Final = "sensor_read_key"


async def get_sensor_config(
    hass: HomeAssistant, user_input: dict[str, str]
) -> PurpleAirConfigEntry:
    """
    Create a new PurpleAirConfigEntry from the user input.

    Required dict keys:
      - CONF_API_READ_KEY: str
      - CONF_SENSOR_ID: str

    Optional dict keys:
      - CONF_SENSOR_READ_KEY: str
    """

    session = async_get_clientsession(hass)

    api_key = config_validation.string(user_input.get(CONF_API_KEY))
    pa_sensor_id = config_validation.string(user_input.get(CONF_ID))
    pa_sensor_read_key = user_input.get(CONF_PA_SENSOR_READ_KEY)

    pa_sensor = await get_api_sensor_config(
        session, api_key, pa_sensor_id, pa_sensor_read_key
    )

    config = PurpleAirConfigEntry(
        pa_sensor_id=pa_sensor.pa_sensor_id,
        title=pa_sensor.name,
        key=pa_sensor.read_key,
        hidden=pa_sensor.hidden,
        api_key=api_key,
        api_version=1,
    )

    _LOGGER.debug("got configuration: %s", config)

    return config


class PurpleAirConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore
    """Configuration flow for setting up a new PurpleAir Sensor."""

    VERSION = 4
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input: dict[str, Any] = None):
        """Handle setup user flow."""

        errors = {}
        if user_input is not None:
            try:
                config = await get_sensor_config(self.hass, user_input)

                await self.async_set_unique_id(config.get_uniqueid())
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=config.title, data=config.asdict())
            except (vol.Invalid, PurpleAirApiUrlError) as error:
                _LOGGER.exception("err", exc_info=error)
                errors["url"] = "url"
            except PurpleAirApiStatusError as error:
                _LOGGER.exception(
                    "PurpleAir API returned bad status code %s\nData:\n%s",
                    error.status,
                    error.text,
                    exc_info=error,
                )
                errors["base"] = "bad_status"
            except PurpleAirApiInvalidResponseError as error:
                _LOGGER.exception(
                    "PurpleAir API returned invalid data.\nMessage: %s\nData: %s",
                    error.message,
                    error.data,
                    exc_info=error,
                )
                errors["base"] = "bad_data"
            except Exception as error:  # pylint: disable=broad-except
                _LOGGER.exception(
                    "An unknown error occurred while setting up the PurpleAir Sensor",
                    exc_info=error,
                )
                errors["base"] = "unknown"

        # see if we can get another PA API key from an existing config to simplify setup.
        api_key = ""
        if not user_input or not user_input.get(CONF_API_KEY):
            entries = self.hass.config_entries.async_entries(DOMAIN)
            keys = {
                e.data.get("api_key")
                for e in entries
                if e.data.get("api_version") == 1 and e.data.get("api_key")
            }

            # only set the key if one exists
            if len(keys) == 1:
                api_key = keys.pop()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY, default=api_key): str,
                vol.Required(CONF_ID): str,
                vol.Optional(CONF_PA_SENSOR_READ_KEY): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

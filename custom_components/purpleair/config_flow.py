# pylint: disable=too-few-public-methods
"""Config flow for Purple Air integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import CONN_CLASS_CLOUD_POLL, ConfigFlow
from homeassistant.const import CONF_URL
from homeassistant.helpers import config_validation
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .model import PurpleAirConfigEntry
from .purple_air_api import get_sensor_configuration
from .purple_air_api.exceptions import (
    PurpleAirApiInvalidResponseError,
    PurpleAirApiStatusError,
    PurpleAirApiUrlError,
)

_LOGGER = logging.getLogger(__name__)


async def get_sensor_config(
    hass: HomeAssistant,
    user_input: dict[str, str]
) -> PurpleAirConfigEntry:
    """
    Gets a PurpleAirConfigEntry for the given user_input. The user_input dict is expected to contain
    an entry for "url".
    """

    session = async_get_clientsession(hass)
    url = config_validation.url(user_input.get('url'))

    pa_sensor = await get_sensor_configuration(session, url)

    config = PurpleAirConfigEntry(
        pa_sensor_id=pa_sensor.pa_sensor_id,
        title=pa_sensor.title,
        key=pa_sensor.key,
        hidden=pa_sensor.key
    )

    _LOGGER.debug('got configuration %s', config)
    return config


class PurpleAirConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configuration flow for setting up a new PurpleAir Sensor."""

    VERSION = 3
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle setup user flow."""

        errors = {}
        if user_input is not None:
            try:
                config = await get_sensor_config(self.hass, user_input)

                await self.async_set_unique_id(config.get_uniqueid())
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=config.title, data=config.asdict())
            except (vol.Invalid, PurpleAirApiUrlError):
                errors["url"] = "url"
            except PurpleAirApiStatusError as error:
                _LOGGER.exception("PurpleAir API returned bad status code %s\nData:\n%s",
                                  error.status, error.text, exc_info=error)
                errors["base"] = "bad_status"
            except PurpleAirApiInvalidResponseError as error:
                _LOGGER.exception("PurpleAir API returned invalid data.\nMessage: %s\nData: %s",
                                  error.message, error.data, exc_info=error)
                errors["base"] = "bad_data"
            except Exception as error:  # pylint: disable=broad-except
                _LOGGER.exception("An unknown error occurred while setting up the PurpleAir Sensor",
                                  exc_info=error)
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_URL): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

"""Config flow for Purple Air integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .model import PurpleAirConfigEntry
from .purple_air_api import get_node_configuration

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    session = async_get_clientsession(hass)
    url = data['url']

    node = {}
    try:
        node = await get_node_configuration(session, url)
    except Exception as error:
        raise PurpleAirConfigError(error) from error

    config = PurpleAirConfigEntry(
        node_id=node.node_id,
        title=node.title,
        key=node.key,
        hidden=node.key
    )

    _LOGGER.debug('got configuration %s', config)
    return config


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PurpleAir."""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle setup user flow."""

        errors = {}
        if user_input is not None:
            try:
                config = await validate_input(self.hass, user_input)

                await self.async_set_unique_id(config.get_uniqueid())
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=config.title, data=config.asdict())
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception as error:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", error)
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_URL): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class PurpleAirConfigError(exceptions.HomeAssistantError):
    """Error to indicate a bad HTTP response."""

    def __init__(self, error):
        self.error = error

"""Config flow for Purple Air integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Final, TypedDict, cast

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

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)

CONF_PA_SENSOR_READ_KEY: Final = "sensor_read_key"


class UserInputSensorConfig(TypedDict):
    """Typed dictionary for "user_input" data."""

    api_key: str
    id: str
    sensor_read_key: str | None


async def get_sensor_config(
    hass: HomeAssistant, user_input: UserInputSensorConfig
) -> PurpleAirConfigEntry:
    """Create a new PurpleAirConfigEntry from the user input."""

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

    _api_key: str
    _new_config: PurpleAirConfigEntry
    _old_config: PurpleAirConfigEntry

    async def async_step_user(
        self, user_input: UserInputSensorConfig = None
    ) -> FlowResult:
        """Handle setup user flow."""

        # if we find an existing API key, send them to the "add_sensor" flow instead.
        api_key = self._get_api_key()
        if api_key:
            self._api_key = api_key
            return await self.async_step_add_sensor()

        errors: dict[str, str] = {}
        if user_input is not None:
            (config, errors) = await self._get_sensor_config(user_input)

            if config and not errors:
                await self.async_set_unique_id(config.get_uniqueid())
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=config.title, data=config.asdict())

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_ID): str,
                vol.Optional(CONF_PA_SENSOR_READ_KEY): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_add_sensor(
        self, user_input: UserInputSensorConfig = None
    ) -> FlowResult:
        """Handle adding another PA sensor with existing API key."""

        errors: dict[str, str] = {}
        if user_input:
            updated_input = cast(UserInputSensorConfig, dict(user_input))
            updated_input["api_key"] = self._api_key
            (config, errors) = await self._get_sensor_config(updated_input)

            if config and not errors:
                await self.async_set_unique_id(config.get_uniqueid())
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=config.title, data=config.asdict())

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ID): str,
                vol.Optional(CONF_PA_SENSOR_READ_KEY): str,
            }
        )

        return self.async_show_form(
            step_id="add_sensor", data_schema=data_schema, errors=errors
        )

    async def async_step_reauth(self, config_data: dict[str, Any]) -> FlowResult:
        """Handle reauthentication requests for PurpleAir sensors.

        The only method currently supported is handling migrations from legacy v0
        sensors to v1 sensors with API keys.
        """

        config = PurpleAirConfigEntry(**config_data)

        # reauth with api_version 0 will always be a legacy migration request
        if config.api_version == 0:
            self._old_config = config
            return self.async_show_form(step_id="legacy_migrate")

        return self.async_abort(reason="unrecognized_reauth")

    async def async_step_legacy_migrate(self, user_input: None = None) -> FlowResult:
        """Handle legacy migration steps for the sensor."""

        # if we have an existing API key, attempt auto migration
        if api_key := self._get_api_key():
            self._api_key = api_key
            return await self.async_step_legacy_migrate_with_api_key()

        return await self.async_step_legacy_migrate_without_api_key()

    async def async_step_legacy_migrate_auto(
        self, user_input: dict[str, Any] = None
    ) -> FlowResult:
        """Automatically migrate the sensor if the user accepts."""
        if user_input is None:
            return self.async_show_form(
                step_id="legacy_migrate_auto", data_schema=None, last_step=True
            )

        return await self._migrate_legacy_config(self._new_config)

    async def async_step_legacy_migrate_with_api_key(
        self, user_input: UserInputSensorConfig | None = None
    ):
        """Attempt to automatically migrate the sensor, if we can.

        Otherwise show the user some configuration steps and hints.
        """

        config = self._old_config
        errors: dict[str, str] = {}

        # attempt automatic authentication
        (new_config, errors) = await self._get_sensor_config(
            {
                "api_key": self._api_key,
                "id": config.pa_sensor_id,
                "sensor_read_key": config.key,
            },
        )

        # self config worked, let the user decide
        if new_config and not errors:
            self._new_config = new_config
            return self.async_show_form(step_id="legacy_migrate_auto", data_schema=None)

        # if we have user_input, auto migrate failed, so try with user provided data
        if user_input is not None:
            (new_config, errors) = await self._get_sensor_config(user_input)

            # if we got a configuration back without errors, migrate the entry
            if new_config and not errors:
                return await self._migrate_legacy_config(new_config)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY, default=config.api_key): str,
                vol.Required(CONF_ID, default=config.pa_sensor_id): str,
                vol.Optional(CONF_PA_SENSOR_READ_KEY, default=config.key): str,
            }
        )

        return self.async_show_form(
            step_id="legacy_migrate_with_api_key",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_legacy_migrate_without_api_key(
        self, user_input: UserInputSensorConfig | None = None
    ) -> FlowResult:
        """Inform the user they need to get an API key to migrate sensors."""

        config = self._old_config
        errors: dict[str, str] = {}

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_ID, default=config.pa_sensor_id): str,
                vol.Optional(CONF_PA_SENSOR_READ_KEY, default=config.key): str,
            }
        )

        return self.async_show_form(
            step_id="legacy_migrate_without_api_key",
            data_schema=data_schema,
            errors=errors,
        )

    def _get_api_key(self) -> str:
        """Attempt to get the API key from existing config entries."""

        api_key = None
        entries = self.hass.config_entries.async_entries(DOMAIN)
        keys = {
            e.data.get("api_key")
            for e in entries
            if e.data.get("api_version") == 1 and e.data.get("api_key")
        }

        # only set the key if one exists
        if len(keys) == 1:
            api_key = keys.pop()

        return api_key or ""

    async def _migrate_legacy_config(
        self, new_config: PurpleAirConfigEntry
    ) -> FlowResult:
        """Update the existing config entry with the new config entry."""

        existing_entry: ConfigEntry = await self.async_set_unique_id(new_config.get_uniqueid())  # type: ignore
        new_entry = new_config.asdict()

        self.hass.config_entries.async_update_entry(existing_entry, data=new_entry)

        self.hass.async_create_task(
            self.hass.config_entries.async_reload(existing_entry.entry_id)
        )

        return self.async_abort(reason="legacy_migrate_success")

    async def _get_sensor_config(
        self, user_input: UserInputSensorConfig
    ) -> tuple[PurpleAirConfigEntry | None, dict[str, str]]:
        errors: dict[str, str] = {}
        try:
            config = await get_sensor_config(self.hass, user_input)
            return (config, errors)
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

        return (None, errors)

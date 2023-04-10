"""Config flow for Purple Air integration."""

from __future__ import annotations

from collections import defaultdict
import logging
from typing import TYPE_CHECKING, Any, Final, TypedDict, cast

import voluptuous as vol

from homeassistant.config_entries import CONN_CLASS_CLOUD_POLL, HANDLERS, ConfigFlow
from homeassistant.const import CONF_API_KEY, CONF_ID
from homeassistant.helpers import config_validation
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .model import PurpleAirConfigEntry
from .purple_air_api.v1.exceptions import PurpleAirApiConfigError
from .purple_air_api.v1.util import get_api_sensor_config

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)

CONF_PA_SENSOR_READ_KEY: Final = "sensor_read_key"


class UserInputSensorConfig(TypedDict):
    """Typed dictionary for "user_input" data."""

    api_key: str
    id: str
    sensor_read_key: str | None


@HANDLERS.register(DOMAIN)
class PurpleAirConfigFlow(ConfigFlow):
    """Configuration flow for setting up a new PurpleAir Sensor."""

    VERSION = 4
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    _api_key: str
    _new_config: PurpleAirConfigEntry
    _old_config: PurpleAirConfigEntry
    _session: ClientSession

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle setup user flow."""

        # if we find an existing API key, send them to the "add_sensor" flow instead.
        api_key = self._get_api_key()
        if api_key:
            self._api_key = api_key
            return await self.async_step_add_sensor()

        errors: dict[str, str] = {}
        if user_input is not None:
            (config, errors) = await self._get_sensor_config(
                cast(UserInputSensorConfig, user_input)
            )

            if config and not errors:
                await self.async_set_unique_id(config.get_uniqueid())
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=config.title, data=config.asdict())

        data = vol_data_dict(user_input)
        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY, default=data[CONF_API_KEY]): str,
                vol.Required(CONF_ID, default=data[CONF_ID]): str,
                vol.Optional(
                    CONF_PA_SENSOR_READ_KEY, default=data[CONF_PA_SENSOR_READ_KEY]
                ): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_add_sensor(
        self, user_input: UserInputSensorConfig | None = None
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

        data = vol_data_dict(user_input)
        data_schema = vol.Schema(
            {
                vol.Required(CONF_ID, default=data[CONF_ID]): str,
                vol.Optional(
                    CONF_PA_SENSOR_READ_KEY, default=data[CONF_PA_SENSOR_READ_KEY]
                ): str,
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

        # we don't use user_input in this method, but it's part of the signature
        del user_input

        # if we have an existing API key, attempt auto migration
        if api_key := self._get_api_key():
            self._api_key = api_key
            return await self.async_step_legacy_migrate_with_api_key()

        return await self.async_step_legacy_migrate_without_api_key()

    async def async_step_legacy_migrate_auto(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Automatically migrate the sensor if the user accepts."""
        if user_input is None:
            return self.async_show_form(
                step_id="legacy_migrate_auto", data_schema=None, last_step=True
            )

        return await self._migrate_legacy_config(self._new_config)

    async def async_step_legacy_migrate_with_api_key(
        self, user_input: UserInputSensorConfig | None = None
    ) -> FlowResult:
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

        data = vol_data_dict(config.as_schema_entry_data(), user_input)
        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY, default=data[CONF_API_KEY]): str,
                vol.Required(CONF_ID, default=data[CONF_ID]): str,
                vol.Optional(
                    CONF_PA_SENSOR_READ_KEY, default=data[CONF_PA_SENSOR_READ_KEY]
                ): str,
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

        if user_input is not None:
            (new_config, errors) = await self._get_sensor_config(user_input)

            if new_config and not errors:
                return await self._migrate_legacy_config(new_config)

        data = vol_data_dict(config.as_schema_entry_data(), user_input)
        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY, default=data[CONF_API_KEY]): str,
                vol.Required(CONF_ID, default=data[CONF_ID]): str,
                vol.Optional(
                    CONF_PA_SENSOR_READ_KEY, default=data[CONF_PA_SENSOR_READ_KEY]
                ): str,
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

    async def _get_sensor_config(
        self, user_input: UserInputSensorConfig
    ) -> tuple[PurpleAirConfigEntry | None, dict[str, str]]:
        """Create a new PurpleAirConfigEntry from the user input."""

        errors: dict[str, str] = {}
        vol_step = ""
        try:
            if not hasattr(self, "_session"):
                self._session = async_get_clientsession(self.hass)

            vol_step = "api_key"
            api_key = config_validation.string(user_input.get(CONF_API_KEY))
            vol_step = "id"
            pa_sensor_id = config_validation.string(user_input.get(CONF_ID))
            pa_sensor_read_key = user_input.get(CONF_PA_SENSOR_READ_KEY)

            pa_sensor = await get_api_sensor_config(
                self._session, api_key, pa_sensor_id, pa_sensor_read_key
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
            return (config, errors)
        except vol.Invalid:
            errors[vol_step] = f"{vol_step}_missing"
        except PurpleAirApiConfigError as error:
            if error.param == "api_key":
                errors["api_key"] = f"api_key_{error.extra}"
            elif error.param == "pa_sensor_id":
                errors["id"] = f"id_{error.extra}"
            elif error.param == "bad_request":
                errors["base"] = "bad_request"
            elif error.param == "server_error":
                errors["base"] = "bad_status"
        except Exception as error:  # pylint: disable=broad-except
            _LOGGER.exception(
                "An unknown error occurred while setting up the PurpleAir Sensor",
                exc_info=error,
            )
            errors["base"] = "unknown"

        return (None, errors)

    async def _migrate_legacy_config(
        self, new_config: PurpleAirConfigEntry
    ) -> FlowResult:
        """Update the existing config entry with the new config entry."""

        existing_entry = await self.async_set_unique_id(new_config.get_uniqueid())
        # try the legacy (bad) format for entries, which was just a sensor id number.
        if not existing_entry:
            existing_entry = await self.async_set_unique_id(new_config.pa_sensor_id)

            if not existing_entry:
                return self.async_abort(reason="unique_id_failure")

        new_entry = new_config.asdict()

        _LOGGER.debug("migrating entry: %s to %s", existing_entry, new_entry)

        self.hass.config_entries.async_update_entry(
            existing_entry, unique_id=new_config.get_uniqueid(), data=new_entry
        )

        self.hass.async_create_task(
            self.hass.config_entries.async_reload(existing_entry.entry_id)
        )

        return self.async_abort(reason="legacy_migrate_success")


def vol_data_dict(*args: Any) -> dict[str, Any]:
    """Create a helpful data dictionary for voluptuous schemas.

    The underlying dictionary will return vol.UNDEFINED for any unset key. The
    *args parameter will update the dictionary with the provided dictionaries in a
    left to right order.

    Example:
    >>> r = None
    >>> s = {"api_key": "abc123", "name": "python"}
    >>> t = {"api_key": "def456"}
    >>> d = vol_data_dict(r, s, t)
    >>> d["api_key"]
    'def456'
    >>> d["name"]
    'python'
    >>> d["other_value"]
    ...
    >>> type(d["other_value"])
    <class 'voluptuous.schema_builder.Undefined'>
    """
    return defaultdict(
        lambda: vol.UNDEFINED,
        {k: v for i in args if i is not None for k, v in i.items() if v is not None},
    )

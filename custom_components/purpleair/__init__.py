"""The PurpleAir integration."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from types import MappingProxyType

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, SCAN_INTERVAL
from .coordinator import PurpleAirDataUpdateCoordinator
from .model import PurpleAirConfigEntry, PurpleAirDomainData
from .purple_air_api import PurpleAirApi
from .purple_air_api.v1.api import PurpleAirApiV1

PARALLEL_UPDATES = 1

PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate configuration entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    # Version 2: use "node_id" as configuration key
    if config_entry.version == 1:
        data = {**config_entry.data}

        data["node_id"] = data["id"]
        del data["id"]

        config_entry.data = MappingProxyType({**data})

        config_entry.version = 2

    # Version 3: use "pa_sensor_id" as configuration key
    if config_entry.version == 2:
        data = {**config_entry.data}

        data["pa_sensor_id"] = data["node_id"]
        del data["node_id"]

        config_entry.data = MappingProxyType({**data})

        config_entry.version = 3

    # Version 4: add "api_version" attribute to flag old (0) or v1 (1) API sensors
    if config_entry.version == 3:
        data = {**config_entry.data}

        data["api_key"] = ""
        data["api_version"] = 0

        config_entry.data = MappingProxyType({**data})

        config_entry.version = 4

    _LOGGER.debug("Migration to version %s successful", config_entry.version)
    return True


async def async_setup(hass: HomeAssistant, config: None) -> bool:
    """Set up the PurpleAir component."""

    # config is unused but required for function signature.
    del config

    entries = hass.config_entries.async_entries(DOMAIN)
    expected_entries_v0 = len({e for e in entries if e.data.get("api_version") == 0})
    expected_entries_v1 = len({e for e in entries if e.data.get("api_version") == 1})

    _LOGGER.info("Adding support for v1 PurpleAir sensors.")

    coordinator_v1 = PurpleAirDataUpdateCoordinator(
        PurpleAirApiV1,
        hass,
        _LOGGER,
        name="purpleair_v1",
        update_interval=timedelta(seconds=SCAN_INTERVAL),
    )

    hass.data[DOMAIN] = PurpleAirDomainData(
        api=None,
        coordinator=None,
        coordinator_v1=coordinator_v1,
        expected_entries=expected_entries_v0,
        expected_entries_v1=expected_entries_v1,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up PurpleAir from a config entry."""

    config = PurpleAirConfigEntry(**config_entry.data)
    domain_data: PurpleAirDomainData = hass.data[DOMAIN]

    if config.api_version == 0 and not domain_data.coordinator:
        _LOGGER.warning("Legacy v0 PurpleAir sensors detected")

        session = async_get_clientsession(hass)
        api_v0 = PurpleAirApi(session)
        coordinator_v0 = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name="purpleair",
            update_method=api_v0.update,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        coordinator_v0.data = {}
        domain_data.api = api_v0
        domain_data.coordinator = coordinator_v0

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, component)
        )

    # remove air_quality entities from the registry if they exist
    ent_reg = entity_registry.async_get(hass)
    unique_id = f"{config_entry.unique_id}_air_quality"
    if entity_id := ent_reg.async_get_entity_id("air_quality", DOMAIN, unique_id):
        _LOGGER.debug("Removing deprecated air_quality entity %s", entity_id)
        ent_reg.async_remove(entity_id)

    # register legacy senors with legacy API
    if config.api_version == 0:
        config_entry.async_start_reauth(hass)
        return await _async_register_legacy_sensor(config, domain_data)

    if config.api_version == 1:
        return await _async_register_v1_sensor(config, domain_data)

    # default failure if api_version is not recognized
    return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unregisters the sensor from the API when the entry is removed."""

    config = PurpleAirConfigEntry(**config_entry.data)
    domain_data: PurpleAirDomainData = hass.data[DOMAIN]

    _LOGGER.debug("unregistering entry %s from api", config.pa_sensor_id)

    # clean up legacy sensors on removal.
    if config.api_version == 0 and (coordinator_v0 := domain_data.coordinator):
        api = hass.data[DOMAIN].api
        api.unregister_sensor(config.pa_sensor_id)

        if config.pa_sensor_id in coordinator_v0.data:
            del coordinator_v0.data[config.pa_sensor_id]

    if config.api_version == 1 and (coordinator_v1 := domain_data.coordinator_v1):
        coordinator_v1.unregister_sensor(config.pa_sensor_id)


async def _async_register_legacy_sensor(
    config: PurpleAirConfigEntry, domain_data: PurpleAirDomainData
) -> bool:
    api_v0 = domain_data.api
    coordinator_v0 = domain_data.coordinator

    if not api_v0 or not coordinator_v0:
        _LOGGER.error(
            "Unable to register PA sensor %s due to invalid domain setup",
            config.pa_sensor_id,
        )
        return False

    api_v0.register_sensor(
        config.pa_sensor_id,
        config.title,
        config.hidden,
        config.key,
    )

    # check for the number of registered sensor during startup to only request
    # an update once all expected sensors are registered.
    if (
        (
            not domain_data.expected_entries  # expected_entries will be 0/None if this is the first one
            or api_v0.get_sensor_count()
            == domain_data.expected_entries  # safety for not spamming at startup
        )
        and (coordinator := domain_data.coordinator)
        and not coordinator.data.get(config.pa_sensor_id)
    ):  # skips refresh if enabling extra sensors
        await coordinator_v0.async_config_entry_first_refresh()
        domain_data.expected_entries = 0

    return True


async def _async_register_v1_sensor(
    config: PurpleAirConfigEntry, domain_data: PurpleAirDomainData
) -> bool:
    coordinator_v1 = domain_data.coordinator_v1

    if not coordinator_v1:
        _LOGGER.error(
            "Unable to register PA sensor %s due to invalid domain setup",
            config.pa_sensor_id,
        )
        return False

    coordinator_v1.register_sensor(
        config.api_key,
        config.pa_sensor_id,
        config.title,
        config.hidden,
        config.key,
    )

    return True

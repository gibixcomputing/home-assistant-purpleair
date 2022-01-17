# pylint: disable=unused-argument
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
from .model import PurpleAirConfigEntry, PurpleAirDomainData
from .purple_air_api import PurpleAirApi

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


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the PurpleAir component."""
    session = async_get_clientsession(hass)

    api = PurpleAirApi(session)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="purpleair",
        update_method=api.update,
        update_interval=timedelta(seconds=SCAN_INTERVAL),
    )

    # prime the coordinator with initial data
    coordinator.data = {}

    entries = hass.config_entries.async_entries(DOMAIN)

    hass.data[DOMAIN] = PurpleAirDomainData(
        api=api,
        coordinator=coordinator,
        expected_entries=len(entries),
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up PurpleAir from a config entry."""

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    # remove air_quality entities from the registry if they exist
    ent_reg = entity_registry.async_get(hass)
    unique_id = f"{entry.unique_id}_air_quality"
    if entity_id := ent_reg.async_get_entity_id("air_quality", DOMAIN, unique_id):
        _LOGGER.debug("Removing deprecated air_quality entity %s", entity_id)
        ent_reg.async_remove(entity_id)

    return True


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
    _LOGGER.debug("unregistering entry %s from api", config.pa_sensor_id)

    api = hass.data[DOMAIN].api
    api.unregister_sensor(config.pa_sensor_id)

    coordinator = hass.data[DOMAIN].coordinator
    if config.pa_sensor_id in coordinator.data:
        del coordinator.data[config.pa_sensor_id]

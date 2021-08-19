"""The PurpleAir integration."""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .purple_air_api import PurpleAirApi

PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate configuration entry."""
    _LOGGER.debug('Migrating from version %s', config_entry.version)

    if config_entry.version == 1:
        data = {**config_entry.data}

        data['node_id'] = data['id']
        del data['id']

        config_entry.data = {**data}

        config_entry.version = 2

    _LOGGER.debug('Migration to version %s successful', config_entry.version)
    return True


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the PurpleAir component."""
    session = async_get_clientsession(hass)

    hass.data[DOMAIN] = PurpleAirApi(hass, session)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up PurpleAir from a config entry."""

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    # remove air_quality entities from the registry if they exist
    ent_reg = entity_registry.async_get(hass)
    unique_id = f'{entry.unique_id}_air_quality'
    if entity_id := ent_reg.async_get_entity_id('air_quality', DOMAIN, unique_id):
        _LOGGER.debug('Removing deprecated air_quality entity %s', entity_id)
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

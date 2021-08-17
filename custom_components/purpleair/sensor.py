""" The Purple Air air_quality platform. """
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DISPATCHER_PURPLE_AIR,
    DOMAIN,
    SENSOR_TYPES,
)

from .model import PurpleAirSensorEntityDescription

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_schedule_add_entities: AddEntitiesCallback
):
    """Creates custom air quality index sensors for Home Assistant."""

    _LOGGER.debug('registring aqi sensor with data: %s', config_entry.data)

    sensors = []

    for description in SENSOR_TYPES:
        sensors.append(PurpleAirSensor(hass, config_entry, description))

    async_schedule_add_entities(sensors)


class PurpleAirSensor(Entity):
    """Provides the calculated Air Quality Index as a separate sensor for Home Assistant."""

    _attr_attribution = 'Data provided by PurpleAir'
    _attr_should_poll = False

    entity_description: PurpleAirSensorEntityDescription

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        description: PurpleAirSensorEntityDescription
    ):
        data = config_entry.data

        self._hass = hass
        self._node_id = data['id']
        self._title = data['title']
        self._key = data['key'] if 'key' in data else None
        self._hidden = data['hidden'] if 'hidden' in data else False

        self._api = hass.data[DOMAIN]
        self._stop_listening = None

        self.entity_description = description

        self._attr_icon = description.icon
        self._attr_name = f'{self._title} {description.name}'
        self._attr_unique_id = f'{self._node_id}_{description.unique_id_suffix}'
        self._attr_unit_of_measurement = description.native_unit_of_measurement
        self._attr_entity_registry_enabled_default = description.enable_default

    @property
    def available(self):
        """Gets whether the sensor is available."""
        return self._api.is_node_registered(self._node_id)

    @property
    def device_info(self):
        return None

    @property
    def state(self):
        """Returns the calculated AQI of the sensor as the current state."""
        return self._api.get_reading(self._node_id, self.entity_description.key)

    async def async_added_to_hass(self):
        """Handles connecting to the dispatcher when the sensor is added to Home Assistant."""

        _LOGGER.debug('registering with node_id: %s', self._node_id)
        self._api.register_node(self._node_id, self._hidden, self._key)

        self._stop_listening = async_dispatcher_connect(
            self._hass,
            DISPATCHER_PURPLE_AIR,
            self.async_write_ha_state
        )

    async def async_will_remove_from_hass(self):
        """Handles cleaning up the dispatcher when the sensor is removed from Home Assistant."""

        _LOGGER.debug('unregistering node_id: %s', self._node_id)
        self._api.unregister_node(self._node_id)

        if self._stop_listening:
            self._stop_listening()
            self._stop_listening = None

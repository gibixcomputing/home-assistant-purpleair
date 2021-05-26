""" The Purple Air air_quality platform. """
import logging

from homeassistant.components.air_quality import AirQualityEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DISPATCHER_PURPLE_AIR, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_schedule_add_entities):
    """Creates air quality sensors for Home Assistant."""

    _LOGGER.debug('registring air quality sensor with data: %s', config_entry.data)

    async_schedule_add_entities([PurpleAirQuality(hass, config_entry)])


class PurpleAirQuality(AirQualityEntity):
    """Provides the air quality entity for Home Assistant."""

    def __init__(self, hass, config_entry):
        data = config_entry.data

        self._hass = hass
        self._node_id = data['id']
        self._title = data['title']
        self._key = data['key'] if 'key' in data else None
        self._hidden = data['hidden'] if 'hidden' in data else False

        self._api = hass.data[DOMAIN]
        self._stop_listening = None

    @property
    def air_quality_index(self):
        """Gets the computed air quality index value."""
        return self._api.get_reading(self._node_id, 'pm2_5_atm_aqi')

    @property
    def attribution(self):
        """Gets the attribution statement."""
        return 'Data provided by PurpleAir'

    @property
    def available(self):
        """Gets whether the sensor is available."""
        return self._api.is_node_registered(self._node_id)

    @property
    def name(self):
        """Gets the sensor name."""
        return self._title

    @property
    def particulate_matter_1_0(self):
        """Gets the Particulate Matter 1.0 value from the API."""
        return self._api.get_reading(self._node_id, 'pm1_0_atm')

    @property
    def particulate_matter_2_5(self):
        """Gets the Particulate Matter 2.5 value from the API."""
        return self._api.get_reading(self._node_id, 'pm2_5_atm')

    @property
    def particulate_matter_10(self):
        """Gets the Particulate Matter 10 value from the API."""
        return self._api.get_reading(self._node_id, 'pm10_0_atm')

    @property
    def should_poll(self):
        """Gets a value indicating the sensor should not be polled."""
        return False

    @property
    def state_attributes(self):
        """Returns the state of the sensor's attributes."""
        attributes = super().state_attributes
        pm1_0 = self.particulate_matter_1_0

        if pm1_0:
            attributes['particulate_matter_1_0'] = pm1_0

        return attributes

    @property
    def unique_id(self):
        """Returns a unique identifier for the sensor."""
        return f'{self._node_id}_air_quality'

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

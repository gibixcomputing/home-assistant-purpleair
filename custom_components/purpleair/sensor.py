""" The Purple Air air_quality platform. """
import logging

from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DISPATCHER_PURPLE_AIR, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_schedule_add_entities):
    """Creates custom air quality index sensors for Home Assistant."""

    _LOGGER.debug('registring aqi sensor with data: %s', config_entry.data)

    async_schedule_add_entities([PurpleAirQualityIndex(hass, config_entry)])


class PurpleAirQualityIndex(Entity):
    """Provides the calculated Air Quality Index as a separate sensor for Home Assistant."""

    def __init__(self, hass, config_entry):
        data = config_entry.data

        self._hass = hass
        self._node_id = data['id']
        self._title = data['title']
        self._api = hass.data[DOMAIN]
        self._stop_listening = None

    @property
    def attribution(self):
        """Gets the attribution statement."""
        return 'Data provided by PurpleAir'

    @property
    def available(self):
        """Gets whether the sensor is available."""
        return self._api.is_node_registered(self._node_id)

    @property
    def icon(self):
        """Gets the icon the sensor should display."""
        return 'mdi:weather-hazy'

    @property
    def name(self):
        """Gets the sensor name."""
        return f'{self._title} Air Quality Index'

    @property
    def should_poll(self):
        """Gets a value indicating the sensor should not be polled."""
        return False

    @property
    def state(self):
        """Returns the calculated AQI of the sensor as the current state."""
        return self._api.get_reading(self._node_id, 'pm2_5_atm_aqi')

    @property
    def unique_id(self):
        """Returns a unique identifier for the sensor."""
        return f'{self._node_id}_air_quality_index'

    @property
    def unit_of_measurement(self):
        """Returns "AQI" as the unit of measurement for the sensor."""
        return 'AQI'

    async def async_added_to_hass(self):
        """Handles connecting to the dispatcher when the sensor is added to Home Assistant."""

        self._stop_listening = async_dispatcher_connect(
            self._hass,
            DISPATCHER_PURPLE_AIR,
            self.async_write_ha_state
        )

    async def async_will_remove_from_hass(self):
        """Handles cleaning up the dispatcher when the sensor is removed from Home Assistant."""

        if self._stop_listening:
            self._stop_listening()
            self._stop_listening = None

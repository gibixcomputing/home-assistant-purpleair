""" The Purple Air air_quality platform. """
import logging

from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.util import dt

from .const import (
    DOMAIN,
    SENSOR_TYPES,
)

from .model import (
    PurpleAirConfigEntry,
    PurpleAirSensorEntityDescription,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_schedule_add_entities: AddEntitiesCallback
):
    """Creates custom air quality index sensors for Home Assistant."""

    config = PurpleAirConfigEntry(**config_entry.data)
    _LOGGER.debug('registring entry with api with sensor with data: %s', config)

    api = hass.data[DOMAIN]['api']
    coordinator = hass.data[DOMAIN]['coordinator']
    expected_entries = hass.data[DOMAIN]['expected_entries']

    dev_registry = device_registry.async_get(hass)
    device = dev_registry.async_get_device({(DOMAIN, config.node_id)})

    if not device or device.model == 'unknown':
        _LOGGER.debug('listening for next update to update device info for node %s', config.node_id)
        unregister = None

        def callback():
            node = coordinator.data.get(config.node_id)
            if not node:
                return

            _LOGGER.debug('updating device info for node %s', config.node_id)

            device = dev_registry.async_get_device({(DOMAIN, config.node_id)})
            _LOGGER.debug('device %s', device)
            dev_registry.async_update_device(
                device.id,
                name=node.get('label') or config.title,
                manufacturer='PurpleAir',
                model=node.get('type'),
                sw_version=node.get('version'),
            )

            _LOGGER.debug('updated device info for node %s', config.node_id)
            unregister()

        unregister = coordinator.async_add_listener(callback)

    sensors = []

    for description in SENSOR_TYPES:
        sensors.append(PurpleAirSensor(config, description, coordinator))

    # register this entry in the API list
    api.register_node(config.node_id, config.hidden, config.key)

    # check for the number of registered nodes during startup to only request an update
    # once all expected nodes are registered.
    if not expected_entries or api.get_node_count() == expected_entries:
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN]['expected_entries'] = None

    async_schedule_add_entities(sensors, not expected_entries)


class PurpleAirSensor(CoordinatorEntity):
    """Provides the calculated Air Quality Index as a separate sensor for Home Assistant."""

    _attr_attribution: Final = 'Data provided by PurpleAir'

    config: PurpleAirConfigEntry
    coordinator: DataUpdateCoordinator
    entity_description: PurpleAirSensorEntityDescription
    node_id: str

    def __init__(
        self,
        config: PurpleAirConfigEntry,
        description: PurpleAirSensorEntityDescription,
        coordinator: DataUpdateCoordinator,
    ):
        super().__init__(coordinator)

        self._attr_device_class = description.device_class
        self._attr_entity_registry_enabled_default: Final = description.enable_default
        self._attr_icon: Final = description.icon
        self._attr_name: Final = f'{config.title} {description.name}'
        self._attr_unique_id: Final = f'{config.node_id}_{description.unique_id_suffix}'
        self._attr_unit_of_measurement: Final = description.native_unit_of_measurement

        self.config = config
        self.coordinator = coordinator
        self.entity_description = description
        self.node_id = config.node_id

        self._warn_stale = False

    @property
    def available(self):
        """Gets whether the sensor is available."""

        node = self.coordinator.data.get(self.node_id)
        available = super().available and node

        if not available:
            return False

        now = dt.utcnow()
        diff = now - node['last_update']

        if diff.seconds > 3600:
            if not self._warn_stale:
                _LOGGER.warning(
                    'PurpleAir Sensor "%s" (%s) has not sent data over an hour. Last update was %s',
                    self.config.title,
                    self.node_id,
                    dt.as_local(node['last_update'])
                )
                self._warn_stale = True

            return False

        self._warn_stale = False
        return True

    @property
    def device_info(self):
        """Gets the device information this sensor is attached to."""
        return {
            'identifiers': {(DOMAIN, self.node_id)},
            'default_name': self.config.title,
            'default_manufacturer': 'PurpleAir',
            'default_model': 'unknown',
        }

    @property
    def extra_state_attributes(self):
        """Gets extra data about the primary sensor (AQI)."""

        if not self.entity_description.primary:
            return None

        node = self.coordinator.data.get(self.node_id)
        if not node:
            return None

        attrs = {
            'last_seen': dt.get_age(node['last_seen']),
            'last_update': dt.as_local(node['last_update']),
            'device_location': node['device_location'],
            'adc': node['adc'],
            'rssi': node['rssi'],
            'uptime': node['uptime'],
        }

        if node['lat'] != 0 and node['lon'] != 0:
            attrs['latitude'] = node['lat']
            attrs['longitude'] = node['lon']

        return attrs

    @property
    def state(self):
        """Returns the calculated AQI of the sensor as the current state."""

        node = self.coordinator.data.get(self.node_id)
        _LOGGER.debug('coordinator node (%s) data: %s', self.node_id, node)
        if not node:
            return None

        readings = node.get('readings')
        if not readings:
            return None

        return readings.get(self.entity_description.key)

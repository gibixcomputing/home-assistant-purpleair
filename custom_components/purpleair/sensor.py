""" The Purple Air air_quality platform. """

import logging

from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
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
    PurpleAirDomainData,
    PurpleAirSensorEntityDescription,
)

PARALLEL_UPDATES = 1

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_schedule_add_entities: AddEntitiesCallback
):
    """Creates custom air quality index sensors for Home Assistant."""

    config = PurpleAirConfigEntry(**config_entry.data)
    _LOGGER.debug('registring entry with api with sensor with data: %s', config)

    domain_data: PurpleAirDomainData = hass.data[DOMAIN]
    api = domain_data.api
    coordinator = domain_data.coordinator
    expected_entries = domain_data.expected_entries

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
            if not device:
                # device has not been registered yet, wait for next update.
                return

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
    api.register_node(config)

    # check for the number of registered nodes during startup to only request an update
    # once all expected nodes are registered.
    if (
        (
            not expected_entries  # expected_entries will be 0/None if this is the first one
            or api.get_node_count() == expected_entries  # safety for not spamming at startup
        )
        and not coordinator.data.get(config.node_id)  # skips refresh if enabling extra sensors
    ):
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN].expected_entries = 0

    async_schedule_add_entities(sensors, False)


class PurpleAirSensor(CoordinatorEntity):  # pylint: disable=too-many-instance-attributes
    """Provides the calculated Air Quality Index as a separate sensor for Home Assistant."""

    _attr_attribution: Final = 'Data provided by PurpleAir'

    config: PurpleAirConfigEntry
    coordinator: DataUpdateCoordinator
    entity_description: PurpleAirSensorEntityDescription
    pa_sensor_id: str

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
        self.pa_sensor_id = config.node_id

        self._warn_readings = False
        self._warn_stale = False

    @property
    def available(self):
        """Gets whether the sensor is available."""

        pa_sensor = self.coordinator.data.get(self.pa_sensor_id)
        if not pa_sensor:
            return False

        now = dt.utcnow()
        diff = now - pa_sensor.last_update

        if diff.seconds > 5400:
            if self.entity_description.primary and not self._warn_stale:
                _LOGGER.warning(
                    'PurpleAir Sensor "%s" (%s) has not sent data over 90 mins. Last update was %s',
                    self.config.title,
                    self.pa_sensor_id,
                    dt.as_local(pa_sensor.last_update)
                )
                self._warn_stale = True

            return False

        if self._get_confidence() == 'invalid':
            if not self._warn_readings:
                _LOGGER.warning(
                    'PurpleAir Sensor "%s" (%s) is returning invalid data',
                    self.config.title,
                    self.pa_sensor_id
                )
                self._warn_readings = True

            return False

        self._warn_readings = False
        self._warn_stale = False
        return True

    @property
    def device_info(self):
        """Gets the device information this sensor is attached to."""
        return {
            'identifiers': {(DOMAIN, self.pa_sensor_id)},
            'default_name': self.config.title,
            'default_manufacturer': 'PurpleAir',
            'default_model': 'unknown',
        }

    @property
    def extra_state_attributes(self):
        """Gets extra data about the primary sensor (AQI)."""

        pa_sensor = self.coordinator.data.get(self.pa_sensor_id)
        if not pa_sensor:
            return None

        confidence = self._get_confidence()

        if not self.entity_description.primary:
            if confidence:
                return {'confidence': confidence}
            return None

        attrs = {
            'last_seen': dt.as_local(pa_sensor.last_seen),
            'last_update': dt.as_local(pa_sensor.last_update),
            'device_location': pa_sensor.device_location,
            'adc': pa_sensor.adc,
            'rssi': pa_sensor.rssi,
            'uptime': pa_sensor.uptime,
        }

        if pa_sensor.lat and pa_sensor.lon:
            attrs[ATTR_LATITUDE] = pa_sensor.lat
            attrs[ATTR_LONGITUDE] = pa_sensor.lon

        if confidence:
            attrs['confidence'] = confidence

        readings = self._get_readings()
        if aqi_status := readings.get(f'{self.entity_description.key}_aqi_status'):
            attrs['aqi_status'] = aqi_status

        return attrs

    @property
    def state(self):
        """Returns the calculated AQI of the sensor as the current state."""

        readings = self._get_readings()
        if not readings:
            return None

        return readings.get(self.entity_description.key)

    def _get_confidence(self):
        readings = self._get_readings()
        key = f'{self.entity_description.key}_confidence'

        return readings.get(key) if readings else None

    def _get_readings(self):
        pa_sensor = self.coordinator.data.get(self.pa_sensor_id)
        return pa_sensor.readings

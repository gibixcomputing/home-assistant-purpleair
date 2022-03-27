"""The Purple Air air_quality platform."""
from __future__ import annotations

import logging
from typing import Dict, Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util import dt

from .const import DOMAIN, SENSOR_TYPES
from .model import (
    PurpleAirConfigEntry,
    PurpleAirDomainData,
    PurpleAirSensorEntityDescription,
)
from .purple_air_api.model import PurpleAirApiSensorData, PurpleAirApiSensorReading
from .sensor_v1 import async_setup_entry as async_setup_entry_v1

PARALLEL_UPDATES = 1

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_schedule_add_entities: AddEntitiesCallback,
):
    """Create custom air quality index sensors for Home Assistant."""

    config = PurpleAirConfigEntry(**config_entry.data)
    _LOGGER.debug("registering entry with api with sensor with data: %s", config)

    domain_data: PurpleAirDomainData = hass.data[DOMAIN]
    coordinator = domain_data.coordinator

    if config.api_version == 0 and (coordinator := domain_data.coordinator):
        pa_sensors = _add_legacy_sensors(hass, config, coordinator)
        async_schedule_add_entities(pa_sensors, False)

    # forward API v1 configs to the v1 sensors.
    if config.api_version == 1:
        await async_setup_entry_v1(hass, config_entry, async_schedule_add_entities)


def _add_legacy_sensors(
    hass: HomeAssistant,
    config: PurpleAirConfigEntry,
    coordinator: DataUpdateCoordinator[dict[str, PurpleAirApiSensorData]],
) -> list[PurpleAirSensor]:
    dev_registry = device_registry.async_get(hass)
    device = dev_registry.async_get_device({(DOMAIN, config.pa_sensor_id)})

    if not device or device.model == "unknown":
        _LOGGER.debug(
            "listening for data to update device info for sensor %s",
            config.pa_sensor_id,
        )

        def callback():
            pa_sensor: PurpleAirApiSensorData | None = coordinator.data.get(
                config.pa_sensor_id
            )
            if not pa_sensor:
                return

            _LOGGER.debug("updating device info for sensor %s", config.pa_sensor_id)

            device = dev_registry.async_get_device({(DOMAIN, config.pa_sensor_id)})
            if not device:
                # device has not been registered yet, wait for next update.
                return

            _LOGGER.debug("device %s", device)
            dev_registry.async_update_device(
                device.id,
                name=config.title or pa_sensor.label,
                manufacturer="PurpleAir",
                model=pa_sensor.type,
                sw_version=pa_sensor.version,
            )

            _LOGGER.debug("updated device info for sensor %s", config.pa_sensor_id)
            unregister()

        unregister = coordinator.async_add_listener(callback)

    pa_sensors: list[PurpleAirSensor] = []

    for description in SENSOR_TYPES:
        pa_sensors.append(PurpleAirSensor(config, description, coordinator))

    return pa_sensors


class PurpleAirSensor(CoordinatorEntity[Dict[str, PurpleAirApiSensorData]]):
    """Provides the calculated Air Quality Index as a separate sensor for Home Assistant."""

    _attr_attribution: Final = "Data provided by PurpleAir"

    config: PurpleAirConfigEntry
    coordinator: DataUpdateCoordinator[dict[str, PurpleAirApiSensorData]]
    entity_description: PurpleAirSensorEntityDescription
    pa_sensor_id: str

    def __init__(
        self,
        config: PurpleAirConfigEntry,
        description: PurpleAirSensorEntityDescription,
        coordinator: DataUpdateCoordinator[dict[str, PurpleAirApiSensorData]],
    ) -> None:
        """Create a new PurpleAirSensor.

        Args:
          config:
              Config entry configuring the sensor.
          description:
              Sensor entity description describing configuration parameters.
          coordinator:
              Coordinator controlling this sensor.
        """
        super().__init__(coordinator)

        self.config = config
        self.entity_description = description
        self.pa_sensor_id = config.pa_sensor_id

        self._attr_name: Final = f"{config.title} {description.name}"
        self._attr_unique_id: Final = (
            f"{config.pa_sensor_id}_{description.unique_id_suffix}"
        )
        self._attr_unit_of_measurement: Final = (  # temporary support for HA < 2021.9
            getattr(description, "native_unit_of_measurement", None)
            or description.unit_of_measurement
        )

        self._warn_readings = False
        self._warn_stale = False

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""

        if not (pa_sensor := self._get_sensor_data()):
            return False

        now = dt.utcnow()
        diff = now - pa_sensor.last_update

        if diff.seconds > 5400:
            if self.entity_description.primary and not self._warn_stale:
                _LOGGER.warning(
                    'PurpleAir Sensor "%s" (%s) has not sent data over 90 mins. Last update was %s',
                    self.config.title,
                    self.pa_sensor_id,
                    dt.as_local(pa_sensor.last_update),
                )
                self._warn_stale = True

            return False

        if self._get_confidence() == "invalid":
            if not self._warn_readings:
                _LOGGER.warning(
                    'PurpleAir Sensor "%s" (%s) is returning invalid data',
                    self.config.title,
                    self.pa_sensor_id,
                )
                self._warn_readings = True

            return False

        self._warn_readings = False
        self._warn_stale = False
        return True

    @property
    def device_info(self) -> dict:
        """Get the device information this sensor is attached to."""
        return {
            "identifiers": {(DOMAIN, self.pa_sensor_id)},
            "default_name": self.config.title,
            "default_manufacturer": "PurpleAir",
            "default_model": "unknown",
        }

    @property
    def extra_state_attributes(self) -> dict | None:
        """Get extra data about the primary sensor (AQI)."""

        if not (pa_sensor := self.coordinator.data.get(self.pa_sensor_id)):
            return None

        confidence = self._get_confidence()

        if not self.entity_description.primary:
            if confidence:
                return {"confidence": confidence}
            return None

        attrs = {
            "last_seen": dt.as_local(pa_sensor.last_seen),
            "last_update": dt.as_local(pa_sensor.last_update),
            "device_location": pa_sensor.device_location,
            "adc": pa_sensor.adc,
            "rssi": pa_sensor.rssi,
            "uptime": pa_sensor.uptime,
        }

        if confidence:
            attrs["confidence"] = confidence

        if readings := self._get_readings():
            if status := readings.get_status(self.entity_description.key):
                attrs["status"] = status

        return attrs

    @property
    def state(self) -> int | float | None:
        """Return the calculated AQI of the sensor as the current state."""

        readings = self._get_readings()
        return readings.get_value(self.entity_description.key) if readings else None

    def _get_confidence(self) -> str | None:
        readings = self._get_readings()
        return (
            readings.get_confidence(self.entity_description.key) if readings else None
        )

    def _get_readings(self) -> PurpleAirApiSensorReading | None:
        pa_sensor = self._get_sensor_data()
        return pa_sensor.readings if pa_sensor else None

    def _get_sensor_data(self) -> PurpleAirApiSensorData | None:
        return self.coordinator.data.get(self.pa_sensor_id)

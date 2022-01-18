"""Sensor entities for v1 API data for Home Assistant."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Dict, Final

from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import DEVICE_CLASS_AQI
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .model import PurpleAirConfigEntry, PurpleAirDomainData
from .purple_air_api.v1.model import NormalizedApiData

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity import Entity
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

    from .purple_air_api.v1.model import SensorReading

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_schedule_add_entities: AddEntitiesCallback,
):
    """Create associated v1 sensors for Home Assistant."""
    config = PurpleAirConfigEntry(**config_entry.data)
    domain_data: PurpleAirDomainData = hass.data[DOMAIN]
    coordinator_v1 = domain_data.coordinator_v1

    if not coordinator_v1:
        _LOGGER.error("Attempting to set up v1 sensors with invalid configuration")
        return

    # we will expose only one AQI sensor here for future 2021.12 option flow
    entities: list[Entity] = [PurpleAirAqiSensor(config, coordinator_v1)]

    async_schedule_add_entities(entities, False)


@dataclass
class PASensorDescription(SensorEntityDescription):
    """Extra properties."""

    suffix: str | None = None


AqiSensorDescription = PASensorDescription(  # type: ignore
    "aqi",
    name="Air Quality Index",
    icon="mdi:weather-hazy",
    device_class=DEVICE_CLASS_AQI,
    state_class=STATE_CLASS_MEASUREMENT,
    native_unit_of_measurement="AQI",
    entity_registry_enabled_default=True,
    suffix="air_quality_index",
)


class PurpleAirAqiSensor(SensorEntity, CoordinatorEntity[Dict[str, NormalizedApiData]]):
    """Provides the AQI value for the configured sensor."""

    _attr_attribution: Final = "Data provided by PurpleAir"

    pa_sensor_id: str
    pa_sensor_name: str

    def __init__(
        self,
        config: PurpleAirConfigEntry,
        coordinator: DataUpdateCoordinator[dict[str, NormalizedApiData]],
    ) -> None:
        """Initialize the AQI sensor."""

        super().__init__(coordinator)

        self.entity_description = AqiSensorDescription
        self.pa_sensor_id = config.pa_sensor_id
        self.pa_sensor_name = config.title

        self._attr_name = f"{self.pa_sensor_name} {self.entity_description.name}"
        self._attr_unique_id = f"{self.pa_sensor_id}_{self.entity_description.suffix}"

    @property
    def available(self) -> bool:
        """Get the sensor availability."""

        if (data := self._get_sensor_data()) and data.pm2_5_aqi_epa:
            return True
        return False

    @property
    def device_info(self) -> dict:
        """Get device information describing this sensor."""
        return {
            "identifiers": {(DOMAIN, self.pa_sensor_id)},
            "default_name": self.pa_sensor_name,
            "default_manufacturer": "PurpleAir",
            "default_model": "unknown",
        }

    @property
    def extra_state_attributes(self) -> dict | None:
        """Get additional state information about the AQI."""

        if not (data := self._get_sensor_data()):
            return None

        return {"status": data.pm2_5_aqi_epa_status}

    @property
    def state(self) -> int | None:
        """Get the AQI value."""

        data = self._get_sensor_data()
        return data.pm2_5_aqi_epa if data else None

    def _get_sensor_data(self) -> SensorReading | None:
        sensor_data = self.coordinator.data.get(self.pa_sensor_id)
        return sensor_data["sensor"] if sensor_data else None

"""Typing definitions for PurpleAir integration."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntityDescription

if TYPE_CHECKING:
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

    from .coordinator import PurpleAirDataUpdateCoordinator
    from .purple_air_api import PurpleAirApi
    from .purple_air_api.model import PurpleAirApiSensorData


@dataclass
class PurpleAirConfigEntry:
    """Class describing the PurpleAir configuration.

    Attributes:
    - hidden (bool):
          Indicates if the current sensor is private.
    - key (str):
          API key needed to access hidden sensor.
    - pa_sensor_id (str):
          Unique id for the sensor.
    - title (str):
          User provided title of the sensor.
    - api_version (int):
          Version of PA API being used.
    - api_key (str):
          Api key used to access the API for this sensor.
          Required if api_version >= 1.
    """

    pa_sensor_id: str
    title: str
    api_version: int
    api_key: str
    hidden: bool = False
    key: str | None = None

    def asdict(self) -> dict:
        """Return the entry as a dict."""
        return asdict(self)

    def as_schema_entry_data(self) -> dict:
        """Return this entry as schema entry data."""
        return {
            "api_key": self.api_key,
            "id": self.pa_sensor_id,
            "sensor_read_key": self.key,
        }

    def get_uniqueid(self) -> str:
        """Get the unique id."""
        return f"purpleair_{self.pa_sensor_id}"


@dataclass
class PurpleAirDomainData:
    """Provides access to data properties stored in the Home Assistant DOMAIN data dict.

    Attributes:
    - api (PurpleAirApi):
          The shared API instance used to query the PurpleAir API.
    - coordinator (DataUpdateCoordinator[dict[str, PurpleAirApiSensorData]]):
          The shared data update coordinator for use with HA sensors.
    - coordinator_v1 ():
          The shared data update coordinator for v1 PA sensors.
    - expected_entries (int=0):
          The number of expected entries to see on startup. Used to minimize the
          number of queries to the API. Set to zero after startup is complete.
    - expected_entries_v1 (int=0):
          The number of expected v1 API entries to see on startup.
    """

    api: PurpleAirApi | None = None
    coordinator: DataUpdateCoordinator[dict[str, PurpleAirApiSensorData]] | None = None
    coordinator_v1: PurpleAirDataUpdateCoordinator | None = None
    expected_entries: int = 0
    expected_entries_v1: int = 0


@dataclass
class PurpleAirSensorEntityDescription(SensorEntityDescription):
    """Class describing PurpleAir sensor entities."""

    device_class: str = ""
    enable_default: bool = False
    primary: bool = False
    unique_id_suffix: str = ""

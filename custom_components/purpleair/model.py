"""Typing definitions for PurpleAir integration."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntityDescription

if TYPE_CHECKING:
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

    from .purple_air_api import PurpleAirApi


@dataclass
class PurpleAirConfigEntry:
    """Class describing the PurpleAir configuration.

    Attributes:
        hidden (bool): Indicates if the current node is private.
        key (str):     API key needed to access hidden nodes.
        node_id (str): Unique id for the node.
        title (str):   User provided title of the node.

    """

    hidden: bool = False
    key: str = None
    node_id: str = None
    title: str = None

    def asdict(self) -> dict:
        """Returns this entry as a dict."""
        return asdict(self)

    def get_uniqueid(self) -> str:
        """Gets the unique id."""
        return f'purpleair_{self.node_id}'


@dataclass
class PurpleAirDomainData():
    """Provides access to data properties stored in the Home Assistant DOMAIN data dict.

    Attributes:
        api              -- The shared API instance used to query the PurpleAir API.
        coordinator      -- The shared data update coordinator for use with HA sensors.
        expected_entries -- The number of expected entries to see on startup. Used to minimize the
                            number of queries to the API. Set to zero after startup is complete.
    """
    api: PurpleAirApi
    coordinator: DataUpdateCoordinator
    expected_entries: int = 0


@dataclass
class PurpleAirSensorEntityDescription(SensorEntityDescription):
    """Class describing PurpleAir sensor entities."""

    device_class: str = None
    enable_default: bool = False
    primary: bool = False
    unique_id_suffix: str = ''

"""Typing definitions for PurpleAir integration."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntityDescription


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


@dataclass
class PurpleAirSensorEntityDescription(SensorEntityDescription):
    """Class describing PurpleAir sensor entities."""

    device_class: str = None
    enable_default: bool = False
    primary: bool = False
    unique_id_suffix: str = ''

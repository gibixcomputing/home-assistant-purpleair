"""Typing definitions for PurpleAir integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import SensorEntityDescription

@dataclass
class PurpleAirSensorEntityDescription(SensorEntityDescription):
    """Class describing PurpleAir sensor entities."""

    enable_default = False

    value: Callable = round

    unique_id_suffix: str = ''

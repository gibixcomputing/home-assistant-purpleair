from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ApiConfigEntry:
    """Describes a configuration entry for the PurpleAir v1 API.

    Attributes:
      pa_sensor_id: ID of the sensor being configured.
      name: Name of the sensor.
      hidden: Flag indicating whether the sensor is private or public.
      key: Sensor read key used when retriving data from a hidden sensor.
    """
    pa_sensor_id: str
    name: str
    hidden: bool
    key: Optional[str] = None

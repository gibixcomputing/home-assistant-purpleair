"""Provides models for the PurpleAir API."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, Dict, Optional, Union


@dataclass
class PurpleAirApiConfigEntry:
    """Describes a configuration entry for the PurpleAir API.

    Attributes:
        pa_sensor_id -- The ID of the sensor being configured
        title        -- The title of the sensor
        hidden       -- Flag indicating whether the sensor is private or public
        key          -- Key used when retrieving sensor data. Must be provided if hidden is True.
    """
    pa_sensor_id: str
    title: str
    hidden: bool
    key: Optional[str] = None


@dataclass
class PurpleAirApiSensorReading:  # pylint: disable=too-many-instance-attributes
    """Represents individual sensor data properties from a PurpleAir Sensor.

    Attributes:
        humidity          -- Corrected humidity reading
        pm10_0_atm        -- Current particulate matter 10.0 reading
        pm1_0_atm         -- Current particulate matter 1.0 reading
        pm2_5_atm         -- Current particulate matter 2.5 reading
        pm2_5_atm_aqi     -- AQI calculated using EPA corrected wildfire formula using PM 2.5 CF=1
        pm2_5_atm_aqi_raw -- AQI calculated using most recent PM 2.5 atmosphere reading
        pm2_5_cf_1        -- PM 2.5 reading using CF=1
        pressure          -- Pressure from the sensor in millibars (hPa)
        temp_f            -- Corrected temperature reading

    Internal Attributes:
        channels   -- Individual channel readings, used during processing
        confidence -- Confidence values for the given readings (good, questionable, single, invalid)
        status     -- Status calculations for EPA AQI sensors
    """

    # sensor data
    humidity: Optional[float] = None
    pm10_0_atm: Optional[float] = None
    pm1_0_atm: Optional[float] = None
    pm2_5_atm: Optional[float] = None
    pm2_5_atm_aqi: Optional[int] = None
    pm2_5_atm_aqi_raw: Optional[int] = None
    pm2_5_cf_1: Optional[float] = None
    pressure: Optional[float] = None
    temp_f: Optional[float] = None

    # additional sensor information
    confidence: dict[str, str] = field(default_factory=dict)
    status: dict[str, str] = field(default_factory=dict)

    # temporary sensor data
    channels: dict[str, dict[str, float]] = field(default_factory=dict)

    def both_channels_have_data(self) -> bool:
        """Determines if both internal channel dictionaries have usable values."""
        channel_a = self.channels.get('A', {})
        channel_b = self.channels.get('B', {})
        a_has_data = bool(channel_a and not all(v is None for v in channel_a.values()))
        b_has_data = bool(channel_b and not all(v is None for v in channel_b.values()))

        return a_has_data and b_has_data

    def clear_temporary_data(self):
        """Clears the temporary channel readings."""
        self.channels.clear()

    def get_channel(self, channel) -> dict[str, float]:
        """
        Gets the internal channel readings dictionary for channel A or B. Raises an AttributeError
        if the channel is not in the set('A', 'B').
        """
        if channel not in ['A', 'B']:
            raise AttributeError('Unsupported channel requested, must be "A" or "B"')

        data = self.channels.get(channel)
        if not data:
            data = {}
            self.channels[channel] = data

        return data

    def get_confidence(self, attr: str) -> str:
        """Gets the given sensor confidence value."""
        return self.confidence.get(attr, '')

    def get_status(self, attr: str) -> str:
        """Gets the given sensor attribute status."""
        return self.status.get(attr, '')

    def get_value(self, attr: str) -> Union[int, float]:
        """Gets the given sensor attribute reading."""
        return getattr(self, attr)

    def set_status(self, attr: str, status: str):
        """Sets the status for the given sensor attribute."""
        self.status[attr] = status

    def set_value(
            self, attr: str, value: Optional[Union[int, float]], confidence: Optional[str] = None
    ):
        """
        Sets the computed value for the given sensor attribute with an optional value and confidence
        rating. An AttributeError is raised if the attribute name does not exist.
        """
        if not hasattr(self, attr):
            raise AttributeError(attr)

        setattr(self, attr, value)
        if confidence:
            self.confidence[attr] = confidence


@dataclass
class PurpleAirApiSensorData:  # pylint: disable=too-many-instance-attributes
    """Represents parsed individual sensor information from the PurpleAir API.

    Attributes:
        pa_sensor_id    -- Registered ID of the PurleAir Sensor
        label           -- API user-defined name of the sensor.
        last_seen       -- Date and time the sensor was last seen according to the API.
        last_update     -- Date and time the sensor last updated according to the API.
        readings        -- Dictonary holding the computed sensor reading data.
        device_location -- Location of the sensor (currently 'indoor', 'outdoor', or 'unknown').
        version         -- Firmware version of the sensor.
        type            -- Type of the air quality sensors in the PurpleAir sensor.
        lat             -- Latitude of the sensor.
        lon             -- Longitude of the sensor.
        rssi            -- Current reported RSSI WiFi signal strength.
        adc             -- Current reported ADC voltage of the sensor.
        uptime          -- Current uptime reported by the sensor.
    """
    pa_sensor_id: str
    label: str
    last_seen: datetime
    last_update: datetime
    readings: PurpleAirApiSensorReading = field(default_factory=PurpleAirApiSensorReading)
    device_location: str = 'unknown'
    version: str = 'unknown'
    type: str = 'unknown'
    lat: Optional[float] = None
    lon: Optional[float] = None
    rssi: float = 0
    adc: float = 0
    uptime: int = 0


@dataclass
class AqiBreakpoint:
    """Describes a breakpoint for calculating AQI.

    Attributes:
        pm_low   -- The low end of particulate matter in ugm3
        pm_high  -- The high end of particulate matter in ugm3
        aqi_low  -- The low end of the calculated AQI
        aqi_high -- The high end of the calculated AQI
    """
    pm_low: float
    pm_high: float
    aqi_low: float
    aqi_high: float


@dataclass
class EpaAvgValue:
    """Provides values for the EPA value cache.

    Attributes:
        hum  -- List of last humidity readings
        pm25 -- List of last PM2.5 CF=1 readings
        timestamp -- Date the value reading was created
    """
    hum: float
    pm25: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


EpaAvgValueCache = Dict[str, Deque[EpaAvgValue]]
PurpleAirApiSensorDataDict = Dict[str, PurpleAirApiSensorData]

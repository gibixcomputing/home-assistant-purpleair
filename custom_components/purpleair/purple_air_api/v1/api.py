"""PurpleAir API v1."""

from __future__ import annotations

from datetime import datetime, timezone
from http import HTTPStatus
import logging
from typing import cast

from aiohttp import ClientSession

from .const import (
    API_FLOAT_VALUES,
    API_INT_VALUES,
    API_SPECIAL_VALUES,
    API_STRING_VALUES,
    API_TIMESTAMP_VALUES,
    URL_API_V1_SENSORS,
)
from .model import ApiConfigEntry, DeviceReading, NormalizedApiData, SensorReading
from .responses import ApiErrorResponse, ApiResponse, ApiSensorResponse

_LOGGER = logging.getLogger(__name__)


class PurpleAirApiV1:
    """Provides access to the PurpleAir v1 API."""

    api_key: str
    sensors: dict[str, ApiConfigEntry]
    session: ClientSession
    _api_issues: bool
    _headers: dict[str, str]
    _last_device_refresh: datetime | None

    def __init__(self, session: ClientSession, api_key: str):
        """Create a new instance of the PurpleAirApiV1 API."""

        self.api_key = api_key
        self.sensors = {}
        self.session = session
        self._api_issues = False
        self._headers = {
            "Accept": "application/json",
            "X-API-Key": api_key,
        }

        _LOGGER.debug("Created v1 API instance for API key: %s", self.api_key)

    def get_sensor_count(self):
        """Get the number of sensors registered with this instance."""
        return len(self.sensors)

    def register_sensor(
        self, pa_sensor_id: str, name: str, hidden: bool, read_key: str | None = None
    ) -> None:
        """Register a PurpleAir sensor with this instance."""

        if pa_sensor_id in self.sensors:
            _LOGGER.debug("detected duplicate registration: %s", pa_sensor_id)
            return

        sensor = ApiConfigEntry(
            pa_sensor_id=pa_sensor_id,
            name=name,
            read_key=read_key,
            hidden=hidden,
        )

        self.sensors[pa_sensor_id] = sensor
        self._last_device_refresh = None
        _LOGGER.debug("registered new sensor: %s", sensor)

    def unregister_sensor(self, pa_sensor_id: str) -> None:
        """Unregister a sensor from this instance."""

        if pa_sensor_id not in self.sensors:
            _LOGGER.debug("detected non-existent unregistration: %s", pa_sensor_id)
            return

        del self.sensors[pa_sensor_id]
        _LOGGER.debug("unregistered sensor: %s", pa_sensor_id)

    async def async_update(self) -> None:
        """Handle updating data from the v1 PurpleAir API."""

        sensor_ids = {s.pa_sensor_id for s in self.sensors.values()}
        read_keys = {
            s.read_key for s in self.sensors.values() if s.hidden and s.read_key
        }

        fields = {
            "sensor_index": -1,
            "rssi": -1,
            "last_seen": -1,
            "channel_state": -1,
            "channel_flags": -1,
            "confidence": -1,
            "humidity": -1,
            "temperature": -1,
            "pressure": -1,
            "pm1.0_atm": -1,
            "pm2.5_atm": -1,
            "pm2.5_cf_1": -1,
            "pm10.0_atm": -1,
            "uptime": -1,
        }

        if self.do_device_update:
            fields["model"] = -1
            fields["hardware"] = -1
            fields["location_type"] = -1
            fields["private"] = -1
            fields["latitude"] = -1
            fields["longitude"] = -1
            fields["firmware_version"] = -1
            fields["firmware_upgrade"] = -1

        params = {
            "fields": ",".join(fields),
            "show_only": ",".join(sensor_ids),
        }

        if read_keys:
            params["read_keys"] = ",".join(sensor_ids)

        async with self.session.get(
            URL_API_V1_SENSORS, headers=self._headers, params=params
        ) as resp:
            if resp.status >= HTTPStatus.INTERNAL_SERVER_ERROR:
                # TODO: raise appropriate error for 5xx response
                _LOGGER.error(
                    "PurpleAir API server error: %s %s", resp.status, resp.reason
                )
                return

            raw_data: ApiResponse = await resp.json()

            if not resp.ok:
                # TODO: raise appropriate error for 4xx response
                error_data = cast(ApiErrorResponse, raw_data)
                _LOGGER.warning(
                    "HTTP not OK. %s %s. error: %s (%s)",
                    resp.status,
                    resp.reason,
                    error_data["description"],
                    error_data["error"],
                )
                return

        _LOGGER.debug("raw data: %s", raw_data)

        data = cast(ApiSensorResponse, raw_data)
        _update_fields_position(fields, data["fields"])
        sensor_data = _read_sensor_data(fields, data, self.do_device_update)

        _LOGGER.debug("sensor data: %s", sensor_data)

    @property
    def do_device_update(self) -> bool:
        """Indicate if this update should include device data."""

        if not self._last_device_refresh:
            return True

        diff = datetime.utcnow() - self._last_device_refresh
        return diff.days >= 1


def _update_fields_position(fields: dict[str, int], api_fields: list[str]) -> None:
    """Map response fields to their index position."""

    for key in fields.keys():
        if key in api_fields:
            fields[key] = api_fields.index(key)

    missing_fields = {field for (field, index) in fields.items() if index == -1}
    if missing_fields:
        for field in missing_fields:
            del fields[field]

        # TODO: hook in to warning system
        _LOGGER.warning(
            "API response did not include requested fields: %s", missing_fields
        )


def _read_sensor_data(
    fields: dict[str, int], data: ApiSensorResponse, include_device_data: bool = False
) -> dict[str, NormalizedApiData]:
    processed_data: dict[str, NormalizedApiData] = {}

    for raw_sensor in data["data"]:
        pa_sensor_id = str(raw_sensor[fields["sensor_index"]])
        sensor_data = SensorReading(pa_sensor_id)
        device_data = DeviceReading(pa_sensor_id) if include_device_data else None

        for field, index in fields.items():
            # skip over the sensor index field
            if field == "sensor_index":
                continue

            value = None

            if field in API_INT_VALUES:
                value = raw_sensor[index]
                value = int(value) if value else None

            if field in API_FLOAT_VALUES:
                value = raw_sensor[index]
                value = float(value) if value else 0.0

            if field in API_STRING_VALUES:
                value = raw_sensor[index]
                value = str(value) if value else ""

            if field in API_TIMESTAMP_VALUES:
                value = raw_sensor[index]
                value = datetime.fromtimestamp(value, timezone.utc) if value else None

            if field in API_SPECIAL_VALUES:
                special_index = raw_sensor[index]
                value = None
                if field == "location_type":
                    value = str(data["location_types"][special_index])
                elif field == "private":
                    value = raw_sensor[index] == "1"
                elif field == "channel_state":
                    value = str(data["channel_states"][special_index])
                elif field == "channel_flags":
                    value = str(data["channel_flags"][special_index])

            sensor_data.set_value(field, value)

            if device_data:
                device_data.set_value(field, value)

        processed_data[pa_sensor_id] = {
            "sensor": sensor_data,
            "device": device_data,
        }

    return processed_data

"""Data update coordinator for PurpleAir v1+ API implementations."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import TYPE_CHECKING, Callable, Dict, Protocol

from aiohttp import ClientSession
from homeassistant.helpers import device_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .purple_air_api.v1.model import NormalizedApiData

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .purple_air_api.v1.model import DeviceReading

_LOGGER = logging.getLogger(__name__)


class ApiProtocol(Protocol):
    """Define the protocol all API implementations must implement."""

    def get_sensor_count(self) -> int:
        """Get registered sensor count from the API."""
        ...

    def register_sensor(
        self, pa_sensor_id: str, name: str, hidden: bool, read_key: str | None = None
    ) -> None:
        """Register a sensor with the API."""
        ...

    def unregister_sensor(self, pa_sensor_id: str) -> None:
        """Unregister a sensor from the API."""
        ...

    async def async_update(
        self, do_device_update: bool
    ) -> dict[str, NormalizedApiData] | None:
        """Update method for the Data Update Coordinator to call."""
        ...


class PurpleAirDataUpdateCoordinator(
    DataUpdateCoordinator[Dict[str, NormalizedApiData]]
):
    """Manage coordination between the API and DataUpdateCoordinator."""

    api: ApiProtocol | None
    _last_device_refresh: datetime | None

    def __init__(
        self, api: Callable[[ClientSession, str], ApiProtocol], *args, **kwargs
    ):
        """Create a new PurpleAirDataUpdateCoordinator.

        The "update_method" keyword argument will be ignored as this will call the
        api.async_update method directly.
        """

        super().__init__(*args, **kwargs)

        self.data: dict[str, NormalizedApiData] = {}
        self.api = None
        self._api_cls = api
        self._last_device_refresh = None

    def register_sensor(
        self,
        api_key: str,
        pa_sensor_id: str,
        name: str,
        hidden: bool,
        read_key: str | None = None,
    ) -> None:
        """Register the sensor with the coordinator and underlying API."""

        if not self.api:
            session = async_get_clientsession(self.hass)
            self.api = self._api_cls(session, api_key)

        self.api.register_sensor(pa_sensor_id, name, hidden, read_key)

        # clear the last device update so we fetch device data next refresh!
        self._last_device_refresh = None

    def unregister_sensor(self, pa_sensor_id: str) -> None:
        """Unregister the sensor from the coordinator and underlying API."""

        if self.api:
            self.api.unregister_sensor(pa_sensor_id)

        if self.get_sensor_count() == 0:
            self.api = None

    def get_sensor_count(self) -> int:
        """Get the registered sensor count from the underlying API."""

        return self.api.get_sensor_count() if self.api else 0

    async def _async_update_data(self) -> dict[str, NormalizedApiData]:
        if not self.api:
            return {}

        data = await self.api.async_update(self.do_device_update)
        if data and [s["device"] for s in data.values() if s["device"]]:
            self._last_device_refresh = datetime.utcnow()

            devices: dict[str, DeviceReading] = {}
            for (pa_sensor_id, api_data) in data.items():
                if device_data := api_data["device"]:
                    devices[pa_sensor_id] = device_data

            self.hass.async_add_job(self._async_update_devices, devices)

        return data if data else {}

    @property
    def do_device_update(self) -> bool:
        """Indicate if this update should include device data."""

        if not self._last_device_refresh:
            return True

        diff = datetime.utcnow() - self._last_device_refresh
        return diff.days >= 1

    async def _async_update_devices(self, devices: dict[str, DeviceReading]) -> None:
        _LOGGER.info("device update! %s", devices)

        config_entries = self.hass.config_entries.async_entries(DOMAIN)

        def find_entry(pa_sensor_id: str) -> ConfigEntry | None:
            if not pa_sensor_id:
                return None

            for config_entry in config_entries:
                if (
                    config_entry.data.get("api_version") == 1
                    and config_entry.data.get("pa_sensor_id") == pa_sensor_id
                ):
                    return config_entry

            return None

        registry = device_registry.async_get(self.hass)

        for (pa_sensor_id, device_data) in devices.items():
            config_entry = find_entry(pa_sensor_id)
            if not config_entry:
                _LOGGER.debug(
                    "could not find matching device for pa_sensor_id: %s", pa_sensor_id
                )
                continue

            _LOGGER.debug(
                "updating device data for pa_sensor_id: %s, config entry: %s",
                pa_sensor_id,
                config_entry.entry_id,
            )

            device = registry.async_get_or_create(
                config_entry_id=config_entry.entry_id,
                identifiers={(DOMAIN, pa_sensor_id)},
                default_name=config_entry.title,
                default_manufacturer="PurpleAir",
                default_model="unknown",
            )

            if device:
                registry.async_update_device(
                    device.id,
                    manufacturer="PurpleAir",
                    model=f"{device_data.model} {device_data.hardware}",
                    sw_version=device_data.firmware_version,
                )

                _LOGGER.debug("updated device for pa_sensor_id: %s", pa_sensor_id)

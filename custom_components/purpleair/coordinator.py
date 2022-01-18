"""Data update coordinator for PurpleAir v1+ API implementations."""

from __future__ import annotations

from typing import Any, Dict, Protocol

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


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

    async def async_update(self):
        """Update method for the Data Update Coordinator to call."""
        ...


class PurpleAirDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Manage coordination between the API and DataUpdateCoordinator."""

    api: ApiProtocol

    def __init__(self, api: ApiProtocol, *args, **kwargs):
        """Create a new PurpleAirDataUpdateCoordinator.

        The "update_method" keyword argument will be ignored as this will call the
        api.async_update method directly.
        """

        super().__init__(*args, **kwargs)

        self.api = api
        self.data: dict[str, Any] = {}

    def register_sensor(
        self, pa_sensor_id: str, name: str, hidden: bool, read_key: str | None = None
    ) -> None:
        """Register the sensor with the coordinator and underlying API."""

        self.api.register_sensor(pa_sensor_id, name, hidden, read_key)

    def unregister_sensor(self, pa_sensor_id: str) -> None:
        """Unregister the sensor from the coordinator and underlying API."""

        self.api.unregister_sensor(pa_sensor_id)

    def get_sensor_count(self) -> int:
        """Get the registered sensor count from the underlying API."""

        return self.api.get_sensor_count()

    async def _async_update_data(self):
        return await self.api.async_update()

"""Typed response dictionaries for PurpleAir API response data."""

from __future__ import annotations

from typing import Any, TypedDict


class ApiResponse(TypedDict):
    """Base API response from v1 PA API."""

    api_version: str
    time_stamp: int


class ApiErrorResponse(ApiResponse):
    """Error API response from v1 PA API."""

    error: str
    description: str


class ApiSensorResponse(ApiResponse):
    """Sensor API response from v1 PA API."""

    data_time_stamp: int
    max_age: int
    firmware_default_version: str
    fields: list[str]
    location_types: list[str]
    channel_states: list[str]
    channel_flags: list[str]
    data: list[list[Any]]

"""Custom types for correios."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from .config_data import CorreiosConfigData
from .diagnostics_entry import CorreiosDiagnosticsEntry
from .diagnostics_package import CorreiosDiagnosticsPackage
from .diagnostics_payload import CorreiosDiagnosticsPayload
from .http_response import CorreiosHttpResponse
from .options_data import CorreiosOptionsData
from .package import CorreiosPackage
from .package_change import CorreiosPackageChange
from .package_change_type import CorreiosPackageChangeType
from .package_direction import CorreiosPackageDirection
from .package_event import CorreiosPackageEvent
from .runtime import CorreiosData

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | Mapping[str, JsonValue]
type JsonObject = Mapping[str, JsonValue]

type CorreiosConfigEntry = ConfigEntry[CorreiosData]
type CorreiosPackages = dict[str, CorreiosPackage]

__all__ = [
    "CorreiosConfigData",
    "CorreiosConfigEntry",
    "CorreiosData",
    "CorreiosDiagnosticsEntry",
    "CorreiosDiagnosticsPackage",
    "CorreiosDiagnosticsPayload",
    "CorreiosHttpResponse",
    "CorreiosOptionsData",
    "CorreiosPackage",
    "CorreiosPackageChange",
    "CorreiosPackageChangeType",
    "CorreiosPackageDirection",
    "CorreiosPackageEvent",
    "CorreiosPackages",
    "JsonObject",
    "JsonPrimitive",
    "JsonValue",
]

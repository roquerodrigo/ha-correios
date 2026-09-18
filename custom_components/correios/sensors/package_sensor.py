"""Sensor exposing the latest status of a single package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity

from ..entity import CorreiosEntity

if TYPE_CHECKING:
    from ..coordinator import CorreiosDataUpdateCoordinator
    from ..data import CorreiosPackage, CorreiosPackageEvent

type PackageAttribute = str | bool | list[dict[str, str | None]] | None

MAX_STATE_LENGTH = 255


def package_sensor_unique_id(entry_id: str, tracking_code: str) -> str:
    """Return the unique id of the sensor that follows ``tracking_code``."""
    return f"{entry_id}_package_{tracking_code.lower()}"


def _event_attributes(event: CorreiosPackageEvent) -> dict[str, str | None]:
    return {
        "description": event.description,
        "detail": event.detail or None,
        "occurred_at": event.occurred_at.isoformat() if event.occurred_at else None,
        "location": event.location or None,
        "destination": event.destination or None,
    }


class CorreiosPackageSensor(CorreiosEntity, SensorEntity):
    """Latest tracking status of one package, named after its tracking code."""

    _attr_translation_key = "package"
    _unrecorded_attributes = frozenset({"events"})

    def __init__(
        self,
        coordinator: CorreiosDataUpdateCoordinator,
        tracking_code: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._tracking_code = tracking_code
        self._attr_translation_placeholders = {"tracking_code": tracking_code}

    @property
    def unique_id(self) -> str:
        """Return a unique id derived from the entry id and the tracking code."""
        return package_sensor_unique_id(
            self.coordinator.config_entry.entry_id, self._tracking_code
        )

    @property
    def package(self) -> CorreiosPackage | None:
        """Return the package this sensor follows, while it is still tracked."""
        return self.packages.get(self._tracking_code)

    @property
    def available(self) -> bool:
        """Report unavailable once the package is no longer tracked."""
        return super().available and self.package is not None

    @property
    def native_value(self) -> str | None:
        """Return the latest status reported for the package."""
        package = self.package
        return package.status[:MAX_STATE_LENGTH] if package is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, PackageAttribute]:
        """Expose the details and the event history of the package."""
        package = self.package
        if package is None:
            return {}
        return {
            "tracking_code": package.tracking_code,
            "direction": package.direction.value,
            "delivered": package.delivered,
            "delayed": package.delayed,
            "detail": package.status_detail or None,
            "location": package.location or None,
            "category": package.category or None,
            "expected_delivery": package.expected_delivery.isoformat()
            if package.expected_delivery
            else None,
            "last_event_at": package.last_event_at.isoformat()
            if package.last_event_at
            else None,
            "events": [_event_attributes(event) for event in package.events],
        }

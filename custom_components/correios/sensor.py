"""Plataforma sensor dos correios."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import callback

from .package_cleanup import CorreiosPackageCleanup
from .sensors import (
    CorreiosNextDeliverySensor,
    CorreiosPackageExpectedDeliverySensor,
    CorreiosPackageSensor,
    CorreiosPackagesInTransitSensor,
    CorreiosPackageTrackingCodeSensor,
    CorreiosSentPackagesInTransitSensor,
)

PACKAGE_SENSOR_CLASSES = (
    CorreiosPackageSensor,
    CorreiosPackageExpectedDeliverySensor,
    CorreiosPackageTrackingCodeSensor,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import CorreiosConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CorreiosConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura os sensores da conta e mantém os sensores de cada pacote rastreado."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            CorreiosPackagesInTransitSensor(coordinator=coordinator),
            CorreiosSentPackagesInTransitSensor(coordinator=coordinator),
            CorreiosNextDeliverySensor(coordinator=coordinator),
        ],
    )

    followed_tracking_codes: set[str] = set()
    package_cleanup = CorreiosPackageCleanup(hass, entry)

    @callback
    def _async_sync_package_sensors() -> None:
        tracked = set(coordinator.data)

        new_tracking_codes = tracked - followed_tracking_codes
        followed_tracking_codes.update(new_tracking_codes)
        async_add_entities(
            sensor_class(coordinator=coordinator, tracking_code=tracking_code)
            for tracking_code in sorted(new_tracking_codes)
            for sensor_class in PACKAGE_SENSOR_CLASSES
        )

        package_cleanup.remove_untracked(tracked)
        followed_tracking_codes.intersection_update(tracked)

    _async_sync_package_sensors()
    entry.async_on_unload(coordinator.async_add_listener(_async_sync_package_sensors))

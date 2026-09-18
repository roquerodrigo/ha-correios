"""Sensor platform for correios."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .sensors import (
    CorreiosNextDeliverySensor,
    CorreiosPackageSensor,
    CorreiosPackagesInTransitSensor,
    CorreiosSentPackagesInTransitSensor,
)
from .sensors.package_sensor import package_sensor_unique_id

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import CorreiosConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CorreiosConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the account sensors and keep one sensor per tracked package."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            CorreiosPackagesInTransitSensor(coordinator=coordinator),
            CorreiosSentPackagesInTransitSensor(coordinator=coordinator),
            CorreiosNextDeliverySensor(coordinator=coordinator),
        ],
    )

    followed_tracking_codes: set[str] = set()

    @callback
    def _async_sync_package_sensors() -> None:
        tracked = set(coordinator.data)

        new_tracking_codes = tracked - followed_tracking_codes
        followed_tracking_codes.update(new_tracking_codes)
        async_add_entities(
            CorreiosPackageSensor(coordinator=coordinator, tracking_code=tracking_code)
            for tracking_code in sorted(new_tracking_codes)
        )

        registry = er.async_get(hass)
        expected_unique_ids = {
            package_sensor_unique_id(entry.entry_id, tracking_code)
            for tracking_code in tracked
        }
        package_prefix = package_sensor_unique_id(entry.entry_id, "")
        for registry_entry in er.async_entries_for_config_entry(
            registry, entry.entry_id
        ):
            if (
                registry_entry.domain == Platform.SENSOR
                and registry_entry.platform == DOMAIN
                and registry_entry.unique_id.startswith(package_prefix)
                and registry_entry.unique_id not in expected_unique_ids
            ):
                registry.async_remove(registry_entry.entity_id)
        followed_tracking_codes.intersection_update(tracked)

    _async_sync_package_sensors()
    entry.async_on_unload(coordinator.async_add_listener(_async_sync_package_sensors))

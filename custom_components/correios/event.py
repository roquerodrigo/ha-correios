"""Event platform for correios."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.event import EventEntity
from homeassistant.core import callback

from .data import CorreiosPackageChangeType
from .entity import CorreiosEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import CorreiosConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CorreiosConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the event platform."""
    async_add_entities(
        [CorreiosPackageUpdateEvent(coordinator=entry.runtime_data.coordinator)],
    )


class CorreiosPackageUpdateEvent(CorreiosEntity, EventEntity):
    """Fires whenever a package shows up, moves or gets delivered."""

    _attr_translation_key = "package_update"
    _attr_event_types = [change_type.value for change_type in CorreiosPackageChangeType]  # noqa: RUF012 -- Home Assistant declares the attribute as a list

    @property
    def unique_id(self) -> str:
        """Return a unique id derived from the config entry id."""
        return f"{self.coordinator.config_entry.entry_id}_package_update"

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Announce every change detected by the latest refresh.

        The state is written once per change because an event entity only keeps
        the last event it was given, and one refresh can move several packages.
        """
        changes = self.coordinator.latest_changes
        if not changes:
            super()._handle_coordinator_update()
            return
        for change in changes:
            package = change.package
            self._trigger_event(
                change.change_type.value,
                {
                    "tracking_code": package.tracking_code,
                    "direction": package.direction.value,
                    "status": package.status,
                    "detail": package.status_detail or None,
                    "location": package.location or None,
                    "expected_delivery": package.expected_delivery.isoformat()
                    if package.expected_delivery
                    else None,
                },
            )
            self.async_write_ha_state()

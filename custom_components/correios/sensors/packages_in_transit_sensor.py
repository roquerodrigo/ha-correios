"""Sensor counting the packages on their way to the account holder."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass

from ..data import CorreiosPackageDirection
from ..entity import CorreiosEntity


class CorreiosPackagesInTransitSensor(CorreiosEntity, SensorEntity):
    """Number of packages addressed to the account holder not yet delivered."""

    _attr_translation_key = "packages_in_transit"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _direction = CorreiosPackageDirection.RECEIVED

    @property
    def unique_id(self) -> str:
        """Return a unique id derived from the config entry id."""
        return f"{self.coordinator.config_entry.entry_id}_{self._attr_translation_key}"

    @property
    def tracking_codes(self) -> list[str]:
        """Return the tracking codes of the packages being counted."""
        return [
            package.tracking_code
            for package in self.packages.values()
            if package.direction is self._direction and not package.delivered
        ]

    @property
    def native_value(self) -> int:
        """Return how many packages are on their way."""
        return len(self.tracking_codes)

    @property
    def extra_state_attributes(self) -> dict[str, list[str]]:
        """Expose which packages make up the count."""
        return {"tracking_codes": self.tracking_codes}

"""Sensor counting the packages the account holder sent."""

from __future__ import annotations

from ..data import CorreiosPackageDirection
from .packages_in_transit_sensor import CorreiosPackagesInTransitSensor


class CorreiosSentPackagesInTransitSensor(CorreiosPackagesInTransitSensor):
    """Number of packages sent by the account holder not yet delivered."""

    _attr_translation_key = "sent_packages_in_transit"
    _direction = CorreiosPackageDirection.SENT

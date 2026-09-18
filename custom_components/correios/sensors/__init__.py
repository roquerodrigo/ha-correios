"""Sensor entities for correios."""

from __future__ import annotations

from .next_delivery_sensor import CorreiosNextDeliverySensor
from .package_sensor import CorreiosPackageSensor
from .packages_in_transit_sensor import CorreiosPackagesInTransitSensor
from .sent_packages_in_transit_sensor import CorreiosSentPackagesInTransitSensor

__all__ = [
    "CorreiosNextDeliverySensor",
    "CorreiosPackageSensor",
    "CorreiosPackagesInTransitSensor",
    "CorreiosSentPackagesInTransitSensor",
]

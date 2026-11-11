"""Entidades de sensor dos correios."""

from __future__ import annotations

from .next_delivery_sensor import CorreiosNextDeliverySensor
from .package_expected_delivery_sensor import CorreiosPackageExpectedDeliverySensor
from .package_sensor import CorreiosPackageSensor
from .package_tracking_code_sensor import CorreiosPackageTrackingCodeSensor
from .packages_in_transit_sensor import CorreiosPackagesInTransitSensor
from .sent_packages_in_transit_sensor import CorreiosSentPackagesInTransitSensor

__all__ = [
    "CorreiosNextDeliverySensor",
    "CorreiosPackageExpectedDeliverySensor",
    "CorreiosPackageSensor",
    "CorreiosPackageTrackingCodeSensor",
    "CorreiosPackagesInTransitSensor",
    "CorreiosSentPackagesInTransitSensor",
]

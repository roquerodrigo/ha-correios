"""Sensor que conta os pacotes enviados pelo titular da conta."""

from __future__ import annotations

from ..data import CorreiosPackageDirection
from .packages_in_transit_sensor import CorreiosPackagesInTransitSensor


class CorreiosSentPackagesInTransitSensor(CorreiosPackagesInTransitSensor):
    """Quantidade de pacotes enviados pelo titular da conta ainda não entregues."""

    _attr_translation_key = "sent_packages_in_transit"
    _direction = CorreiosPackageDirection.SENT

"""Sensor que expõe a previsão de entrega de um único pacote."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.util import dt as dt_util

from ..package_entity import CorreiosPackageEntity

if TYPE_CHECKING:
    from datetime import datetime


class CorreiosPackageExpectedDeliverySensor(CorreiosPackageEntity, SensorEntity):
    """
    Previsão de entrega de um pacote.

    Como a próxima entrega da conta, é um sensor ``timestamp`` no início do dia
    previsto, para que a interface o formate conforme o idioma do usuário.
    """

    _package_key = "expected_delivery"
    _attr_translation_key = "package_expected_delivery"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        """Retorna o início do dia previsto para a entrega do pacote."""
        package = self.package
        if package is None or package.expected_delivery is None:
            return None
        return dt_util.start_of_local_day(package.expected_delivery)

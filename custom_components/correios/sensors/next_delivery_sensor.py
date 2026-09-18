"""Sensor que expõe a previsão de entrega mais próxima."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from ..data import CorreiosPackageDirection
from ..entity import CorreiosEntity

if TYPE_CHECKING:
    from datetime import date

    from ..data import CorreiosPackage


class CorreiosNextDeliverySensor(CorreiosEntity, SensorEntity):
    """Previsão de entrega mais próxima entre os pacotes a caminho."""

    _attr_translation_key = "next_delivery"
    _attr_device_class = SensorDeviceClass.DATE

    @property
    def unique_id(self) -> str:
        """Retorna um unique id derivado do id da config entry."""
        return f"{self.coordinator.config_entry.entry_id}_next_delivery"

    @property
    def next_package(self) -> CorreiosPackage | None:
        """Retorna o pacote previsto para chegar primeiro, se algum tiver data."""
        expected = [
            package
            for package in self.packages.values()
            if package.direction is CorreiosPackageDirection.RECEIVED
            and not package.delivered
            and package.expected_delivery is not None
        ]
        return min(
            expected,
            key=lambda package: (str(package.expected_delivery), package.tracking_code),
            default=None,
        )

    @property
    def native_value(self) -> date | None:
        """Retorna a previsão de entrega mais próxima."""
        package = self.next_package
        return package.expected_delivery if package is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Expõe a qual pacote a data pertence."""
        package = self.next_package
        return {"tracking_code": package.tracking_code if package else None}

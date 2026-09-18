"""Sensor que expõe a previsão de entrega mais próxima."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.util import dt as dt_util

from ..data import CorreiosPackageDirection
from ..entity import CorreiosEntity

if TYPE_CHECKING:
    from datetime import datetime

    from ..data import CorreiosPackage


class CorreiosNextDeliverySensor(CorreiosEntity, SensorEntity):
    """
    Previsão de entrega mais próxima entre os pacotes a caminho.

    É um sensor ``timestamp``, e não ``date``: a interface do Home Assistant só
    formata o estado conforme o idioma e as preferências do usuário para
    timestamps; um sensor ``date`` é exibido como ``AAAA-MM-DD`` em qualquer
    card. A previsão não tem hora, então vale o início do dia no fuso do Home
    Assistant.
    """

    _attr_translation_key = "next_delivery"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

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
    def native_value(self) -> datetime | None:
        """Retorna o início do dia da previsão de entrega mais próxima."""
        package = self.next_package
        if package is None or package.expected_delivery is None:
            return None
        return dt_util.start_of_local_day(package.expected_delivery)

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Expõe a qual pacote a data pertence."""
        package = self.next_package
        if package is None or package.expected_delivery is None:
            return {"tracking_code": None, "expected_delivery": None}
        return {
            "tracking_code": package.tracking_code,
            "expected_delivery": package.expected_delivery.isoformat(),
        }

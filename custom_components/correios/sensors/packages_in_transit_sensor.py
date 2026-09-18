"""Sensor que conta os pacotes a caminho do titular da conta."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass

from ..data import CorreiosPackageDirection
from ..entity import CorreiosEntity


class CorreiosPackagesInTransitSensor(CorreiosEntity, SensorEntity):
    """Quantidade de pacotes endereçados ao titular da conta ainda não entregues."""

    _attr_translation_key = "packages_in_transit"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _direction = CorreiosPackageDirection.RECEIVED

    @property
    def unique_id(self) -> str:
        """Retorna um unique id derivado do id da config entry."""
        return f"{self.coordinator.config_entry.entry_id}_{self._attr_translation_key}"

    @property
    def tracking_codes(self) -> list[str]:
        """Retorna os códigos de rastreamento dos pacotes contados."""
        return [
            package.tracking_code
            for package in self.packages.values()
            if package.direction is self._direction and not package.delivered
        ]

    @property
    def native_value(self) -> int:
        """Retorna quantos pacotes estão a caminho."""
        return len(self.tracking_codes)

    @property
    def extra_state_attributes(self) -> dict[str, list[str]]:
        """Expõe quais pacotes compõem a contagem."""
        return {"tracking_codes": self.tracking_codes}

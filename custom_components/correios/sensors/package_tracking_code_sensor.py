"""Sensor que expõe o número de rastreio de um único pacote."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory

from ..package_entity import CorreiosPackageEntity


class CorreiosPackageTrackingCodeSensor(CorreiosPackageEntity, SensorEntity):
    """Número de rastreio de um pacote."""

    _package_key = "tracking_code"
    _attr_translation_key = "package_tracking_code"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str:
        """Retorna o código de rastreamento do pacote."""
        return self._tracking_code

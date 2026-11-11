"""Classe base CorreiosEntity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import CorreiosDataUpdateCoordinator
from .devices import CorreiosAccountDevice

if TYPE_CHECKING:
    from homeassistant.helpers.device_registry import ChildDeviceInfo, DeviceInfo

    from .data import CorreiosPackages


class CorreiosEntity(CoordinatorEntity[CorreiosDataUpdateCoordinator]):
    """Entidade base dos Correios."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo | ChildDeviceInfo:
        """Retorna o device info da conta que a config entry representa."""
        return CorreiosAccountDevice(self.coordinator.config_entry).info

    @property
    def packages(self) -> CorreiosPackages:
        """Retorna os pacotes rastreados, vazio antes da primeira atualização."""
        data: CorreiosPackages | None = self.coordinator.data
        return data if data is not None else {}

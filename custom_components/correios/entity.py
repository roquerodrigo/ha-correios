"""Classe base CorreiosEntity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, TRACKING_PAGE_URL
from .coordinator import CorreiosDataUpdateCoordinator

if TYPE_CHECKING:
    from .data import CorreiosPackages


class CorreiosEntity(CoordinatorEntity[CorreiosDataUpdateCoordinator]):
    """Entidade base dos Correios."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Retorna o device info da conta que a config entry representa."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name=f"Correios {self.coordinator.config_entry.title}",
            manufacturer="Correios",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=TRACKING_PAGE_URL,
        )

    @property
    def packages(self) -> CorreiosPackages:
        """Retorna os pacotes rastreados, vazio antes da primeira atualização."""
        data: CorreiosPackages | None = self.coordinator.data
        return data if data is not None else {}

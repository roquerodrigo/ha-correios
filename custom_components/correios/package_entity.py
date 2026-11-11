"""Classe base das entidades que pertencem a um pacote rastreado."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .devices import CorreiosPackageDevice
from .entity import CorreiosEntity

if TYPE_CHECKING:
    from homeassistant.helpers.device_registry import ChildDeviceInfo

    from .coordinator import CorreiosDataUpdateCoordinator
    from .data import CorreiosPackage


def package_entity_unique_id(
    entry_id: str, tracking_code: str, key: str | None = None
) -> str:
    """Retorna o unique id da entidade ``key`` do pacote ``tracking_code``."""
    unique_id = f"{entry_id}_package_{tracking_code.lower()}"
    return f"{unique_id}_{key}" if key else unique_id


class CorreiosPackageEntity(CorreiosEntity):
    """Entidade de um pacote, no subdispositivo dele."""

    _package_key: str | None = None

    def __init__(
        self,
        coordinator: CorreiosDataUpdateCoordinator,
        tracking_code: str,
    ) -> None:
        """Inicializa com o código de rastreamento do pacote."""
        super().__init__(coordinator)
        self._tracking_code = tracking_code

    @property
    def unique_id(self) -> str:
        """Retorna um unique id derivado do id da entry e do código de rastreamento."""
        return package_entity_unique_id(
            self.coordinator.config_entry.entry_id,
            self._tracking_code,
            self._package_key,
        )

    @property
    def device_info(self) -> ChildDeviceInfo:
        """Retorna o pacote como subdispositivo do dispositivo da conta."""
        return CorreiosPackageDevice(
            self._tracking_code,
            self.coordinator.config_entry.runtime_data.account_device_id,
        ).info

    @property
    def package(self) -> CorreiosPackage | None:
        """Retorna o pacote desta entidade, enquanto ele for rastreado."""
        return self.packages.get(self._tracking_code)

    @property
    def available(self) -> bool:
        """Fica indisponível quando o pacote deixa de ser rastreado."""
        return super().available and self.package is not None

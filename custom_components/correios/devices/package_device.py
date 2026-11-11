"""Subdispositivo que representa um pacote rastreado."""

from __future__ import annotations

from homeassistant.helpers.device_registry import ChildDeviceInfo

from ..const import DOMAIN


class CorreiosPackageDevice:
    """Pacote rastreado, aninhado sob o dispositivo da conta."""

    def __init__(self, tracking_code: str, account_device_id: str) -> None:
        """Inicializa com o código de rastreamento e o dispositivo da conta."""
        self._tracking_code = tracking_code
        self._account_device_id = account_device_id

    @staticmethod
    def identifier_for(tracking_code: str) -> tuple[str, str]:
        """Retorna o identificador do subdispositivo de ``tracking_code``."""
        return (DOMAIN, tracking_code)

    @property
    def info(self) -> ChildDeviceInfo:
        """Retorna o device info do pacote como subdispositivo da conta."""
        return ChildDeviceInfo(
            identifiers={self.identifier_for(self._tracking_code)},
            parent_device_id=self._account_device_id,
            translation_key="package",
            translation_placeholders={"tracking_code": self._tracking_code},
        )

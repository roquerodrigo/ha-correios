"""Dispositivo que representa a conta de uma config entry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from ..const import DOMAIN, TRACKING_PAGE_URL

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from ..data import CorreiosConfigEntry


class CorreiosAccountDevice:
    """
    Dispositivo da conta, sob o qual cada pacote rastreado é um subdispositivo.

    Um subdispositivo só pode ser registrado depois do dispositivo pai, e as
    plataformas adicionam as suas entidades em paralelo; por isso o dispositivo
    da conta é registrado antes de as plataformas serem carregadas.
    """

    def __init__(self, entry: CorreiosConfigEntry) -> None:
        """Inicializa com a config entry que a conta representa."""
        self._entry = entry

    @property
    def identifier(self) -> tuple[str, str]:
        """Retorna o identificador do dispositivo no device registry."""
        return (DOMAIN, self._entry.entry_id)

    @property
    def info(self) -> DeviceInfo:
        """Retorna o device info da conta."""
        return DeviceInfo(
            identifiers={self.identifier},
            name=f"Correios {self._entry.title}",
            manufacturer="Correios",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=TRACKING_PAGE_URL,
        )

    def register(self, hass: HomeAssistant) -> str:
        """Registra o dispositivo da conta e retorna o id dele no device registry."""
        device = dr.async_get(hass).async_get_or_create(
            config_entry_id=self._entry.entry_id,
            **self.info,
        )
        return device.id

"""Remoção dos pacotes que deixaram de ser rastreados."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .devices import CorreiosPackageDevice
from .package_entity import package_entity_unique_id

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

    from homeassistant.core import HomeAssistant

    from .data import CorreiosConfigEntry


class CorreiosPackageCleanup:
    """
    Remove os subdispositivos e os sensores dos pacotes que saíram do payload.

    Excluir o subdispositivo também exclui os sensores dele. Os sensores sem
    subdispositivo são de versões anteriores, que os criavam no dispositivo da
    conta, e de um pacote que saiu da listagem antes da atualização. O pacote
    de um sensor é o trecho do unique id que segue o prefixo, até o próximo
    ``_``, porque um código de rastreamento não tem ``_``.
    """

    def __init__(self, hass: HomeAssistant, entry: CorreiosConfigEntry) -> None:
        """Inicializa com a config entry cujos pacotes são conferidos."""
        self._hass = hass
        self._entry = entry

    def remove_untracked(self, tracked_codes: AbstractSet[str]) -> None:
        """Remove tudo o que pertence a pacotes fora de ``tracked_codes``."""
        self._remove_untracked_devices(tracked_codes)
        self._remove_untracked_sensors(tracked_codes)

    def _remove_untracked_devices(self, tracked_codes: AbstractSet[str]) -> None:
        registry = dr.async_get(self._hass)
        expected_identifiers = {
            CorreiosPackageDevice.identifier_for(tracking_code)
            for tracking_code in tracked_codes
        }
        for device in dr.async_child_entries_for_config_entry(
            registry, self._entry.entry_id
        ):
            if not device.identifiers & expected_identifiers:
                registry.async_remove_device(device.id)

    def _remove_untracked_sensors(self, tracked_codes: AbstractSet[str]) -> None:
        registry = er.async_get(self._hass)
        tracked = {tracking_code.lower() for tracking_code in tracked_codes}
        package_prefix = package_entity_unique_id(self._entry.entry_id, "")
        for registry_entry in er.async_entries_for_config_entry(
            registry, self._entry.entry_id
        ):
            if (
                registry_entry.domain == Platform.SENSOR
                and registry_entry.platform == DOMAIN
                and registry_entry.unique_id.startswith(package_prefix)
                and registry_entry.unique_id.removeprefix(package_prefix).split("_")[0]
                not in tracked
            ):
                registry.async_remove(registry_entry.entity_id)

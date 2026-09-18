"""Suporte a diagnostics dos correios."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

if TYPE_CHECKING:
    from collections.abc import Mapping

    from homeassistant.core import HomeAssistant

    from .data import (
        CorreiosConfigEntry,
        CorreiosDiagnosticsEntry,
        CorreiosDiagnosticsPackage,
        CorreiosDiagnosticsPayload,
        CorreiosPackage,
        CorreiosPackages,
    )

TO_REDACT: frozenset[str] = frozenset({CONF_PASSWORD, CONF_USERNAME})


def _package_diagnostics(package: CorreiosPackage) -> CorreiosDiagnosticsPackage:
    """Descreve um pacote sem o código de rastreamento nem detalhes em texto livre."""
    return {
        "direction": package.direction.value,
        "delivered": package.delivered,
        "delayed": package.delayed,
        "status": package.status,
        "location": package.location,
        "category": package.category,
        "expected_delivery": package.expected_delivery.isoformat()
        if package.expected_delivery
        else None,
        "last_event_at": package.last_event_at.isoformat()
        if package.last_event_at
        else None,
        "event_count": len(package.events),
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CorreiosConfigEntry,
) -> CorreiosDiagnosticsPayload:
    """Retorna o diagnostics de uma config entry."""
    redacted_data = cast(
        "Mapping[str, str]",
        async_redact_data(dict(entry.data), set(TO_REDACT)),
    )
    diag_entry: CorreiosDiagnosticsEntry = {
        "title": entry.title,
        "version": entry.version,
        "domain": entry.domain,
        "data": redacted_data,
        "options": cast("Mapping[str, str | int]", dict(entry.options)),
    }
    packages: CorreiosPackages | None = entry.runtime_data.coordinator.data
    return {
        "entry": diag_entry,
        "packages": [
            _package_diagnostics(package) for package in (packages or {}).values()
        ],
    }

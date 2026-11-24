"""Suporte a diagnostics dos correios."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import (
        CorreiosConfigEntry,
        CorreiosDiagnosticsEntry,
        CorreiosDiagnosticsPackage,
        CorreiosDiagnosticsPayload,
        CorreiosPackage,
        CorreiosPackages,
    )

# O título da entrada é derivado do login: CPF parcial, CNPJ ou e-mail.
TO_REDACT: frozenset[str] = frozenset({CONF_PASSWORD, CONF_USERNAME, "title"})


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
    diag_entry = cast(
        "CorreiosDiagnosticsEntry",
        async_redact_data(
            {
                "title": entry.title,
                "version": entry.version,
                "domain": entry.domain,
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            set(TO_REDACT),
        ),
    )
    packages: CorreiosPackages | None = entry.runtime_data.coordinator.data
    return {
        "entry": diag_entry,
        "packages": [
            _package_diagnostics(package) for package in (packages or {}).values()
        ],
    }

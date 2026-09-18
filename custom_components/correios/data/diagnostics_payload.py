"""Estrutura tipada do retorno de async_get_config_entry_diagnostics."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from .diagnostics_entry import CorreiosDiagnosticsEntry
    from .diagnostics_package import CorreiosDiagnosticsPackage


class CorreiosDiagnosticsPayload(TypedDict):
    """Estrutura do retorno de async_get_config_entry_diagnostics."""

    entry: CorreiosDiagnosticsEntry
    packages: list[CorreiosDiagnosticsPackage]

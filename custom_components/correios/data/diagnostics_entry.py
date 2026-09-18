"""Seção tipada da entry no dump de diagnostics."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from collections.abc import Mapping


class CorreiosDiagnosticsEntry(TypedDict):
    """Seção da entry no dump de diagnostics."""

    title: str
    version: int
    domain: str
    data: Mapping[str, str]
    options: Mapping[str, str | int]

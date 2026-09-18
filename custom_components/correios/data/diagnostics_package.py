"""Seção tipada de pacote no dump de diagnostics."""

from __future__ import annotations

from typing import TypedDict


class CorreiosDiagnosticsPackage(TypedDict):
    """Um pacote como exposto no diagnostics, sem os campos que o identificam."""

    direction: str
    delivered: bool
    delayed: bool
    status: str
    location: str
    category: str
    expected_delivery: str | None
    last_event_at: str | None
    event_count: int

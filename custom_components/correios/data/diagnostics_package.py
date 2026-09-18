"""Typed package section of the diagnostics dump."""

from __future__ import annotations

from typing import TypedDict


class CorreiosDiagnosticsPackage(TypedDict):
    """A package as exposed in diagnostics, without identifying fields."""

    direction: str
    delivered: bool
    delayed: bool
    status: str
    location: str
    category: str
    expected_delivery: str | None
    last_event_at: str | None
    event_count: int

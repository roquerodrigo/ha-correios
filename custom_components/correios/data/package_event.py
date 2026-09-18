"""A single tracking event in the history of a package."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class CorreiosPackageEvent:
    """One step of the route a package went through."""

    code: str
    description: str
    detail: str
    occurred_at: datetime | None
    location: str
    destination: str

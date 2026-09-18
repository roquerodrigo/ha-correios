"""Um pacote rastreado pela conta dos Correios."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date, datetime

    from .package_direction import CorreiosPackageDirection
    from .package_event import CorreiosPackageEvent


@dataclass(frozen=True)
class CorreiosPackage:
    """Última situação conhecida de um pacote e o seu histórico de eventos."""

    tracking_code: str
    direction: CorreiosPackageDirection
    delivered: bool
    delayed: bool
    status: str
    status_detail: str
    location: str
    category: str
    expected_delivery: date | None
    last_event_at: datetime | None
    events: tuple[CorreiosPackageEvent, ...]

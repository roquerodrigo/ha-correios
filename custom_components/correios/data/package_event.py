"""Um único evento de rastreamento no histórico de um pacote."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class CorreiosPackageEvent:
    """Uma etapa do trajeto percorrido por um pacote."""

    code: str
    description: str
    detail: str
    occurred_at: datetime | None
    location: str
    destination: str

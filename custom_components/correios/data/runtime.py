"""Dados de runtime guardados em entry.runtime_data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.loader import Integration

    from ..api import CorreiosApiClient
    from ..coordinator import CorreiosDataUpdateCoordinator


@dataclass
class CorreiosData:
    """Dados guardados em entry.runtime_data para os Correios."""

    client: CorreiosApiClient
    coordinator: CorreiosDataUpdateCoordinator
    integration: Integration

"""Runtime data stored on entry.runtime_data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.loader import Integration

    from ..api import CorreiosApiClient
    from ..coordinator import CorreiosDataUpdateCoordinator


@dataclass
class CorreiosData:
    """Data stored on entry.runtime_data for the Correios."""

    client: CorreiosApiClient
    coordinator: CorreiosDataUpdateCoordinator
    integration: Integration

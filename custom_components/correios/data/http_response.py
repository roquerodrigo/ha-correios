"""Uma resposta HTTP já lida da rede."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yarl import URL


@dataclass(frozen=True)
class CorreiosHttpResponse:
    """Status, URL final após redirecionamentos e corpo decodificado da resposta."""

    status: int
    url: URL
    body: str

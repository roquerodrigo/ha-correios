"""An HTTP response already read from the wire."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yarl import URL


@dataclass(frozen=True)
class CorreiosHttpResponse:
    """Status, final URL after redirects and decoded body of a response."""

    status: int
    url: URL
    body: str

"""Classes de exceção do cliente da API dos correios."""

from __future__ import annotations

from .api_client_authentication_error import (
    CorreiosApiClientAuthenticationError,
)
from .api_client_communication_error import (
    CorreiosApiClientCommunicationError,
)
from .api_client_error import CorreiosApiClientError

__all__ = [
    "CorreiosApiClientAuthenticationError",
    "CorreiosApiClientCommunicationError",
    "CorreiosApiClientError",
]

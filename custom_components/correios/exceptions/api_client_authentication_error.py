"""Authentication error raised by the API client."""

from __future__ import annotations

from .api_client_error import CorreiosApiClientError


class CorreiosApiClientAuthenticationError(
    CorreiosApiClientError,
):
    """Exception to indicate an authentication error."""

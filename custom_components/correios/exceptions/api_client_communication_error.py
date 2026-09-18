"""Erro de comunicação lançado pelo cliente da API."""

from __future__ import annotations

from .api_client_error import CorreiosApiClientError


class CorreiosApiClientCommunicationError(
    CorreiosApiClientError,
):
    """Exceção que indica um erro de comunicação."""

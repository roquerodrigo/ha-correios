"""Erro de autenticação lançado pelo cliente da API."""

from __future__ import annotations

from .api_client_error import CorreiosApiClientError


class CorreiosApiClientAuthenticationError(
    CorreiosApiClientError,
):
    """Exceção que indica um erro de autenticação."""

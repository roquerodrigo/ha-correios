"""Erro lançado quando a listagem paginada expira durante a leitura."""

from __future__ import annotations

from .api_client_error import CorreiosApiClientError


class CorreiosApiClientListingExpiredError(
    CorreiosApiClientError,
):
    """Exceção que indica que o site descartou a listagem entre uma página e outra."""

"""Estrutura tipada das credenciais persistidas na config entry."""

from __future__ import annotations

from typing import TypedDict


class CorreiosConfigData(TypedDict):
    """Estrutura das credenciais persistidas na config entry."""

    username: str
    password: str

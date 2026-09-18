"""Estrutura tipada das opções graváveis pelo options flow."""

from __future__ import annotations

from typing import NotRequired, TypedDict


class CorreiosOptionsData(TypedDict, total=False):
    """Estrutura das opções graváveis pelo options flow."""

    scan_interval: NotRequired[int]
    delivered_retention_days: NotRequired[int]

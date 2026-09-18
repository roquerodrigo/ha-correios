"""Direção de um pacote em relação ao titular da conta."""

from __future__ import annotations

from enum import StrEnum


class CorreiosPackageDirection(StrEnum):
    """Indica se o titular da conta recebe ou envia o pacote."""

    RECEIVED = "received"
    SENT = "sent"

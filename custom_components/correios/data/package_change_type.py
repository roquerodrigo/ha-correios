"""Tipos de mudança detectados entre duas atualizações consecutivas."""

from __future__ import annotations

from enum import StrEnum


class CorreiosPackageChangeType(StrEnum):
    """O que aconteceu com um pacote desde a atualização anterior."""

    NEW_PACKAGE = "new_package"
    STATUS_CHANGED = "status_changed"
    DELIVERED = "delivered"

"""Kinds of change detected between two consecutive refreshes."""

from __future__ import annotations

from enum import StrEnum


class CorreiosPackageChangeType(StrEnum):
    """What happened to a package since the previous refresh."""

    NEW_PACKAGE = "new_package"
    STATUS_CHANGED = "status_changed"
    DELIVERED = "delivered"

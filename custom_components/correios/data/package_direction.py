"""Direction of a package relative to the account holder."""

from __future__ import annotations

from enum import StrEnum


class CorreiosPackageDirection(StrEnum):
    """Whether the account holder receives or sends the package."""

    RECEIVED = "received"
    SENT = "sent"

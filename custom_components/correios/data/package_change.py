"""A change detected on a package between two consecutive refreshes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .package import CorreiosPackage
    from .package_change_type import CorreiosPackageChangeType


@dataclass(frozen=True)
class CorreiosPackageChange:
    """A package together with what changed about it."""

    change_type: CorreiosPackageChangeType
    package: CorreiosPackage

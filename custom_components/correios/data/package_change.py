"""Uma mudança detectada em um pacote entre duas atualizações consecutivas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .package import CorreiosPackage
    from .package_change_type import CorreiosPackageChangeType


@dataclass(frozen=True)
class CorreiosPackageChange:
    """Um pacote junto com o que mudou nele."""

    change_type: CorreiosPackageChangeType
    package: CorreiosPackage

"""Detecta o que mudou nos pacotes rastreados entre duas atualizações."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .data import CorreiosPackageChange, CorreiosPackageChangeType

if TYPE_CHECKING:
    from .data import CorreiosPackage, CorreiosPackages


def detect_package_changes(
    previous: CorreiosPackages | None,
    current: CorreiosPackages,
) -> tuple[CorreiosPackageChange, ...]:
    """
    Retorna as mudanças que vale anunciar, na ordem em que os pacotes são listados.

    Nada é reportado sem um snapshot anterior: na primeira atualização todo
    pacote pareceria novo, e anunciar o histórico inteiro a cada reinicialização
    é ruído, não notícia.
    """
    if previous is None:
        return ()
    changes: list[CorreiosPackageChange] = []
    for tracking_code, package in current.items():
        change_type = _change_type(previous.get(tracking_code), package)
        if change_type is not None:
            changes.append(
                CorreiosPackageChange(change_type=change_type, package=package)
            )
    return tuple(changes)


def _change_type(
    before: CorreiosPackage | None,
    after: CorreiosPackage,
) -> CorreiosPackageChangeType | None:
    if before is None:
        return CorreiosPackageChangeType.NEW_PACKAGE
    if after.delivered and not before.delivered:
        return CorreiosPackageChangeType.DELIVERED
    if (after.status, after.last_event_at) != (before.status, before.last_event_at):
        return CorreiosPackageChangeType.STATUS_CHANGED
    return None

"""Detect what changed on the tracked packages between two refreshes."""

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
    Return the changes worth announcing, in the order the packages are listed.

    Nothing is reported without a previous snapshot: on the first refresh every
    package would look new, and announcing the whole history on each restart is
    noise rather than news.
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

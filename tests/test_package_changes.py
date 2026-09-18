from __future__ import annotations

from dataclasses import replace

from custom_components.correios.data import CorreiosPackageChangeType
from custom_components.correios.package_changes import detect_package_changes

from .conftest import IN_TRANSIT_CODE


def test_first_snapshot_announces_nothing(packages):
    assert detect_package_changes(None, packages) == ()


def test_identical_snapshots_announce_nothing(packages):
    assert detect_package_changes(dict(packages), packages) == ()


def test_unknown_package_is_new(packages):
    previous = {
        code: package for code, package in packages.items() if code != IN_TRANSIT_CODE
    }
    changes = detect_package_changes(previous, packages)
    assert [(c.change_type, c.package.tracking_code) for c in changes] == [
        (CorreiosPackageChangeType.NEW_PACKAGE, IN_TRANSIT_CODE)
    ]


def test_status_change_is_detected(packages):
    current = dict(packages)
    current[IN_TRANSIT_CODE] = replace(
        packages[IN_TRANSIT_CODE], status="Objeto saiu para entrega ao destinatário"
    )
    changes = detect_package_changes(packages, current)
    assert [c.change_type for c in changes] == [
        CorreiosPackageChangeType.STATUS_CHANGED
    ]


def test_delivery_wins_over_status_change(packages):
    current = dict(packages)
    current[IN_TRANSIT_CODE] = replace(
        packages[IN_TRANSIT_CODE],
        status="Objeto entregue ao destinatário",
        delivered=True,
    )
    changes = detect_package_changes(packages, current)
    assert [c.change_type for c in changes] == [CorreiosPackageChangeType.DELIVERED]


def test_package_leaving_the_list_announces_nothing(packages):
    current = {
        code: package for code, package in packages.items() if code != IN_TRANSIT_CODE
    }
    assert detect_package_changes(packages, current) == ()

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

from custom_components.correios.const import DOMAIN
from custom_components.correios.coordinator import (
    FAILURE_GRACE_PERIOD,
    CorreiosDataUpdateCoordinator,
)
from custom_components.correios.data import CorreiosPackageChangeType
from custom_components.correios.exceptions import (
    CorreiosApiClientAuthenticationError,
    CorreiosApiClientError,
)

from .conftest import DELIVERED_CODE, IN_TRANSIT_CODE, LONG_DELIVERED_CODE


def _make_coordinator(hass, packages=None, retention_days=7):
    coord = CorreiosDataUpdateCoordinator(
        hass=hass,
        scan_interval=timedelta(minutes=15),
        delivered_retention=timedelta(days=retention_days),
    )
    client = AsyncMock()
    client.async_get_packages = AsyncMock(return_value=packages or {})
    runtime_data = type("D", (), {"client": client})()
    coord.config_entry = type(
        "E", (), {"entry_id": "eid", "runtime_data": runtime_data}
    )()
    return coord, client


def test_init_sets_name_and_interval(hass):
    coord, _ = _make_coordinator(hass)
    assert coord.name == DOMAIN
    assert coord.update_interval == timedelta(minutes=15)


async def test_update_keeps_packages_in_transit_and_recently_delivered(hass, packages):
    coord, _ = _make_coordinator(hass, packages)
    result = await coord._async_update_data()
    assert IN_TRANSIT_CODE in result
    assert DELIVERED_CODE in result
    assert LONG_DELIVERED_CODE not in result


async def test_zero_retention_drops_every_delivered_package(hass, packages):
    coord, _ = _make_coordinator(hass, packages, retention_days=0)
    assert DELIVERED_CODE not in await coord._async_update_data()


async def test_delivered_package_without_a_date_is_dropped(hass, packages):
    undated = {DELIVERED_CODE: replace(packages[DELIVERED_CODE], last_event_at=None)}
    coord, _ = _make_coordinator(hass, undated)
    assert await coord._async_update_data() == {}


async def test_first_update_reports_no_changes(hass, packages):
    coord, _ = _make_coordinator(hass, packages)
    await coord._async_update_data()
    assert coord.latest_changes == ()


async def test_update_reports_changes_against_previous_data(hass, packages):
    coord, client = _make_coordinator(hass, packages)
    coord.data = await coord._async_update_data()
    moved = dict(packages)
    moved[IN_TRANSIT_CODE] = replace(
        packages[IN_TRANSIT_CODE], status="Saiu para entrega"
    )
    client.async_get_packages.return_value = moved
    await coord._async_update_data()
    assert [change.change_type for change in coord.latest_changes] == [
        CorreiosPackageChangeType.STATUS_CHANGED
    ]


async def test_update_raises_auth_failed_on_auth_error(hass, packages):
    coord, client = _make_coordinator(hass)
    coord.data = packages
    client.async_get_packages.side_effect = CorreiosApiClientAuthenticationError("no")
    with pytest.raises(ConfigEntryAuthFailed):
        await coord._async_update_data()


async def test_update_serves_last_known_data_within_grace_period(hass, packages):
    coord, client = _make_coordinator(hass)
    coord.data = packages
    coord.latest_changes = ("stale",)
    client.async_get_packages.side_effect = CorreiosApiClientError("blip")
    assert await coord._async_update_data() == packages
    assert coord.latest_changes == ()


async def test_update_raises_update_failed_after_grace_period(hass, packages):
    coord, client = _make_coordinator(hass)
    coord.data = packages
    client.async_get_packages.side_effect = CorreiosApiClientError("down")
    coord._first_failure_at = (
        dt_util.utcnow() - FAILURE_GRACE_PERIOD - timedelta(seconds=1)
    )
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()


async def test_update_raises_update_failed_without_previous_data(hass):
    coord, client = _make_coordinator(hass)
    client.async_get_packages.side_effect = CorreiosApiClientError("down")
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()


async def test_update_clears_failure_window_after_success(hass, packages):
    coord, _ = _make_coordinator(hass, packages)
    coord._first_failure_at = dt_util.utcnow()
    await coord._async_update_data()
    assert coord._first_failure_at is None

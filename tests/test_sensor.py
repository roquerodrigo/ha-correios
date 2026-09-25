from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from unittest.mock import MagicMock

from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.correios.const import DOMAIN
from custom_components.correios.coordinator import MISSING_PACKAGE_GRACE_PERIOD
from custom_components.correios.sensors import (
    CorreiosNextDeliverySensor,
    CorreiosPackageSensor,
    CorreiosPackagesInTransitSensor,
    CorreiosSentPackagesInTransitSensor,
)

from .conftest import (
    DELIVERED_CODE,
    IN_TRANSIT_CODE,
    LONG_DELIVERED_CODE,
    SECOND_IN_TRANSIT_CODE,
    SENT_CODE,
)


def _coordinator(data):
    coordinator = MagicMock()
    coordinator.data = data
    coordinator.config_entry.entry_id = "eid"
    return coordinator


async def _refresh(hass, entry):
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=16))
    await hass.async_block_till_done()


async def test_platform_creates_account_and_package_sensors(hass, setup_integration):
    assert hass.states.get("sensor.correios_456_789_packages_in_transit").state == "2"
    assert (
        hass.states.get("sensor.correios_456_789_sent_packages_in_transit").state == "1"
    )
    assert (
        hass.states.get("sensor.correios_456_789_next_delivery").state
        == dt_util.start_of_local_day(date(2026, 9, 20))
        .astimezone(dt_util.UTC)
        .isoformat()
    )
    assert len(hass.states.async_all("sensor")) == 3 + 4


async def test_package_sensor_state_and_attributes(hass, setup_integration):
    state = hass.states.get(
        f"sensor.correios_456_789_package_{IN_TRANSIT_CODE.lower()}"
    )
    assert state.state == "Objeto em transferência - por favor aguarde"
    assert state.attributes["tracking_code"] == IN_TRANSIT_CODE
    assert state.attributes["direction"] == "received"
    assert state.attributes["delivered"] is False
    assert state.attributes["location"] == "Valinhos - SP"
    assert state.attributes["expected_delivery"] == "2026-09-25"
    assert state.attributes["detail"] is None
    assert len(state.attributes["events"]) == 2
    assert state.attributes["events"][0]["destination"] == "Sao Paulo - SP"
    assert state.attributes["events"][1]["destination"] is None


async def test_long_delivered_package_gets_no_sensor(hass, setup_integration):
    assert (
        hass.states.get(
            f"sensor.correios_456_789_package_{LONG_DELIVERED_CODE.lower()}"
        )
        is None
    )


async def test_new_package_gets_a_sensor_on_refresh(
    hass, setup_integration, mock_api_client, packages
):
    grown = dict(packages)
    grown["EE666666666BR"] = replace(
        packages[IN_TRANSIT_CODE], tracking_code="EE666666666BR"
    )
    mock_api_client.async_get_packages.return_value = grown
    await _refresh(hass, setup_integration)
    assert hass.states.get("sensor.correios_456_789_package_ee666666666br") is not None
    assert hass.states.get("sensor.correios_456_789_packages_in_transit").state == "3"


async def test_package_missing_for_a_moment_keeps_its_sensor(
    hass, setup_integration, mock_api_client, packages
):
    entity_id = f"sensor.correios_456_789_package_{DELIVERED_CODE.lower()}"
    shrunk = {
        code: package for code, package in packages.items() if code != DELIVERED_CODE
    }
    mock_api_client.async_get_packages.return_value = shrunk
    await _refresh(hass, setup_integration)
    assert er.async_get(hass).async_get(entity_id) is not None
    assert hass.states.get(entity_id).state == packages[DELIVERED_CODE].status


async def test_package_missing_beyond_grace_period_loses_its_sensor(
    hass, setup_integration, mock_api_client, packages
):
    shrunk = {
        code: package for code, package in packages.items() if code != DELIVERED_CODE
    }
    mock_api_client.async_get_packages.return_value = shrunk
    await _refresh(hass, setup_integration)
    coordinator = setup_integration.runtime_data.coordinator
    coordinator._missing_since = dict.fromkeys(
        coordinator._missing_since,
        dt_util.utcnow() - MISSING_PACKAGE_GRACE_PERIOD - timedelta(seconds=1),
    )
    await _refresh(hass, setup_integration)
    entity_id = f"sensor.correios_456_789_package_{DELIVERED_CODE.lower()}"
    assert er.async_get(hass).async_get(entity_id) is None
    assert hass.states.get(entity_id) is None


async def test_stale_registry_entry_is_removed_on_setup(
    hass, mock_api_client, enable_custom_integrations
):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="***.456.789-**",
        data={"username": "12345678909", "password": "pass"},
        unique_id="12345678909",
    )
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    stale = registry.async_get_or_create(
        "sensor", DOMAIN, f"{entry.entry_id}_package_zz999999999br", config_entry=entry
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert registry.async_get(stale.entity_id) is None
    assert registry.async_get("sensor.correios_456_789_packages_in_transit") is not None


def test_in_transit_sensor_counts_only_received_packages(packages):
    sensor = CorreiosPackagesInTransitSensor(coordinator=_coordinator(packages))
    assert sensor.native_value == 2
    assert sensor.extra_state_attributes == {
        "tracking_codes": [IN_TRANSIT_CODE, SECOND_IN_TRANSIT_CODE]
    }
    assert sensor.unique_id == "eid_packages_in_transit"


def test_sent_sensor_counts_only_sent_packages(packages):
    sensor = CorreiosSentPackagesInTransitSensor(coordinator=_coordinator(packages))
    assert sensor.native_value == 1
    assert sensor.extra_state_attributes == {"tracking_codes": [SENT_CODE]}
    assert sensor.unique_id == "eid_sent_packages_in_transit"


def test_count_sensors_are_zero_before_first_refresh():
    assert (
        CorreiosPackagesInTransitSensor(coordinator=_coordinator(None)).native_value
        == 0
    )


def test_next_delivery_picks_the_earliest_date(packages):
    sensor = CorreiosNextDeliverySensor(coordinator=_coordinator(packages))
    assert sensor.native_value == dt_util.start_of_local_day(date(2026, 9, 20))
    assert sensor.native_value.tzinfo is not None
    assert sensor.extra_state_attributes == {
        "tracking_code": SECOND_IN_TRANSIT_CODE,
        "expected_delivery": "2026-09-20",
    }
    assert sensor.unique_id == "eid_next_delivery"


def test_next_delivery_is_none_without_packages():
    sensor = CorreiosNextDeliverySensor(coordinator=_coordinator({}))
    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {
        "tracking_code": None,
        "expected_delivery": None,
    }


def test_package_sensor_without_its_package_is_unavailable():
    sensor = CorreiosPackageSensor(coordinator=_coordinator({}), tracking_code="GONE")
    assert sensor.available is False
    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}
    assert sensor.unique_id == "eid_package_gone"

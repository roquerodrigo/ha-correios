from __future__ import annotations

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.correios.const import DOMAIN

from .conftest import DELIVERED_CODE, IN_TRANSIT_CODE, LONG_DELIVERED_CODE


def _account_device(hass, entry):
    return dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, entry.entry_id), entry.entry_id
    )


def _package_device(hass, entry, tracking_code):
    return dr.async_get(hass).async_get_child_device_by_identifier(
        (DOMAIN, tracking_code), entry.entry_id
    )


async def test_setup_stores_the_account_device_id(hass, setup_integration):
    account = _account_device(hass, setup_integration)
    assert account is not None
    assert setup_integration.runtime_data.account_device_id == account.id


async def test_each_package_is_a_child_of_the_account_device(
    hass, setup_integration, packages
):
    account = _account_device(hass, setup_integration)
    children = dr.async_entries_for_parent_device(dr.async_get(hass), account.id)
    assert {identifier for child in children for identifier in child.identifiers} == {
        (DOMAIN, tracking_code) for tracking_code in packages
    } - {(DOMAIN, LONG_DELIVERED_CODE)}


async def test_package_device_is_named_after_its_tracking_code(hass, setup_integration):
    device = _package_device(hass, setup_integration, IN_TRANSIT_CODE)
    assert device is not None
    assert device.name == f"Package {IN_TRANSIT_CODE}"


async def test_package_sensor_lives_on_its_package_device(hass, setup_integration):
    entity = er.async_get(hass).async_get(
        f"sensor.correios_456_789_package_{IN_TRANSIT_CODE.lower()}"
    )
    device = _package_device(hass, setup_integration, IN_TRANSIT_CODE)
    assert entity.device_id == device.id
    state = hass.states.get(entity.entity_id)
    assert state.attributes["friendly_name"] == f"Package {IN_TRANSIT_CODE}"


async def test_account_sensors_stay_on_the_account_device(hass, setup_integration):
    entity = er.async_get(hass).async_get("sensor.correios_456_789_packages_in_transit")
    assert entity.device_id == _account_device(hass, setup_integration).id


async def test_package_sensor_on_the_account_device_moves_to_its_package_device(
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
    account = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, entry.entry_id)}
    )
    registry = er.async_get(hass)
    legacy = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{entry.entry_id}_package_{DELIVERED_CODE.lower()}",
        config_entry=entry,
        device_id=account.id,
        suggested_object_id=f"correios_legacy_package_{DELIVERED_CODE.lower()}",
    )

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    migrated = registry.async_get(legacy.entity_id)
    assert migrated is not None
    assert migrated.device_id == _package_device(hass, entry, DELIVERED_CODE).id
    assert hass.states.get(legacy.entity_id).state == "Objeto entregue ao destinatário"

from __future__ import annotations

from unittest.mock import MagicMock

from homeassistant.helpers.device_registry import DeviceEntryType

from custom_components.correios.const import ATTRIBUTION, DOMAIN
from custom_components.correios.entity import CorreiosEntity


def _make_entity(data=None) -> CorreiosEntity:
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "my_id"
    coordinator.config_entry.title = "***.456.789-**"
    coordinator.data = data
    return CorreiosEntity(coordinator=coordinator)


def test_class_level_attributes():
    entity = _make_entity()
    assert entity._attr_attribution == ATTRIBUTION
    assert entity._attr_has_entity_name is True


def test_device_info_describes_the_account():
    device_info = _make_entity().device_info
    assert device_info["name"] == "Correios ***.456.789-**"
    assert device_info["manufacturer"] == "Correios"
    assert device_info["entry_type"] is DeviceEntryType.SERVICE
    assert device_info["identifiers"] == {(DOMAIN, "my_id")}


def test_packages_is_empty_before_first_refresh():
    assert _make_entity(data=None).packages == {}


def test_packages_returns_coordinator_data(packages):
    assert _make_entity(data=packages).packages is packages

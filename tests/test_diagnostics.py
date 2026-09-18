from __future__ import annotations

from custom_components.correios.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics_redacts_username(hass, setup_integration):
    diag = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert diag["entry"]["data"]["username"] == "**REDACTED**"


async def test_diagnostics_redacts_password(hass, setup_integration):
    diag = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert diag["entry"]["data"]["password"] == "**REDACTED**"


async def test_diagnostics_includes_entry_metadata(hass, setup_integration):
    diag = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert diag["entry"]["domain"] == "correios"
    assert diag["entry"]["version"] == 1
    assert "title" in diag["entry"]


async def test_diagnostics_lists_packages_without_tracking_codes(
    hass, setup_integration
):
    diag = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert len(diag["packages"]) == 4
    assert all("tracking_code" not in package for package in diag["packages"])
    first = diag["packages"][0]
    assert first["direction"] == "received"
    assert first["expected_delivery"] == "2026-09-25"
    assert first["event_count"] == 2
    assert "BR" not in str(diag)


async def test_diagnostics_handles_missing_dates(hass, setup_integration, packages):
    from dataclasses import replace

    code, package = next(iter(packages.items()))
    setup_integration.runtime_data.coordinator.data = {
        code: replace(package, expected_delivery=None, last_event_at=None)
    }
    diag = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert diag["packages"][0]["expected_delivery"] is None
    assert diag["packages"][0]["last_event_at"] is None


async def test_diagnostics_options_redacted_when_present(hass, setup_integration):
    diag = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert isinstance(diag["entry"]["options"], dict)

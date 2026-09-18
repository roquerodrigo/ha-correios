"""Correios integration for Home Assistant."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, cast

from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import CorreiosApiClient
from .card_registration import CorreiosCardRegistration
from .const import (
    CONF_DELIVERED_RETENTION_DAYS,
    DEFAULT_DELIVERED_RETENTION_DAYS,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
)
from .coordinator import CorreiosDataUpdateCoordinator
from .data import CorreiosData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.device_registry import DeviceEntry

    from .data import CorreiosConfigData, CorreiosConfigEntry

PLATFORMS: list[Platform] = [Platform.EVENT, Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CorreiosConfigEntry,
) -> bool:
    """Set up Correios from a config entry."""
    config = cast("CorreiosConfigData", entry.data)
    scan_interval_seconds: int = int(
        entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS),
    )
    delivered_retention_days: int = int(
        entry.options.get(
            CONF_DELIVERED_RETENTION_DAYS, DEFAULT_DELIVERED_RETENTION_DAYS
        ),
    )
    coordinator = CorreiosDataUpdateCoordinator(
        hass=hass,
        scan_interval=timedelta(seconds=scan_interval_seconds),
        delivered_retention=timedelta(days=delivered_retention_days),
        config_entry=entry,
    )
    entry.runtime_data = CorreiosData(
        client=CorreiosApiClient(
            username=config["username"],
            password=config["password"],
            session=async_create_clientsession(hass),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    await coordinator.async_config_entry_first_refresh()

    await CorreiosCardRegistration(
        hass, str(entry.runtime_data.integration.version)
    ).async_register()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: CorreiosConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(
    hass: HomeAssistant,
    entry: CorreiosConfigEntry,
) -> None:
    """Clean up the card registration when the last entry is removed."""
    if hass.config_entries.async_entries(DOMAIN):
        return
    integration = async_get_loaded_integration(hass, entry.domain)
    await CorreiosCardRegistration(hass, str(integration.version)).async_remove()


async def async_reload_entry(
    hass: HomeAssistant,
    entry: CorreiosConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant,  # noqa: ARG001 -- part of the signature Home Assistant calls
    entry: CorreiosConfigEntry,
    device_entry: DeviceEntry,
) -> bool:
    """
    Allow deleting devices this entry no longer provides.

    Home Assistant hides the "delete device" button unless the integration
    implements this hook. The account device is refused because the next
    refresh would recreate it; anything else left behind is allowed to go.
    """
    return (DOMAIN, entry.entry_id) not in device_entry.identifiers

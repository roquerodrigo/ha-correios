from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from .conftest import IN_TRANSIT_CODE, SECOND_IN_TRANSIT_CODE

EVENT_ENTITY_ID = "event.correios_456_789_package_update"


async def _refresh(hass):
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=16))
    await hass.async_block_till_done()


async def test_event_entity_starts_without_an_event(hass, setup_integration):
    assert hass.states.get(EVENT_ENTITY_ID).state == "unknown"


async def test_status_change_fires_an_event(
    hass, setup_integration, mock_api_client, packages
):
    moved = dict(packages)
    moved[IN_TRANSIT_CODE] = replace(
        packages[IN_TRANSIT_CODE], status="Objeto saiu para entrega ao destinatário"
    )
    mock_api_client.async_get_packages.return_value = moved
    await _refresh(hass)
    state = hass.states.get(EVENT_ENTITY_ID)
    assert state.attributes["event_type"] == "status_changed"
    assert state.attributes["tracking_code"] == IN_TRANSIT_CODE
    assert state.attributes["status"] == "Objeto saiu para entrega ao destinatário"
    assert state.attributes["expected_delivery"] == "2026-09-25"


async def test_every_change_of_a_refresh_is_written(
    hass, setup_integration, mock_api_client, packages
):
    moved = dict(packages)
    moved[IN_TRANSIT_CODE] = replace(packages[IN_TRANSIT_CODE], status="Em rota")
    moved[SECOND_IN_TRANSIT_CODE] = replace(
        packages[SECOND_IN_TRANSIT_CODE],
        status="Objeto entregue ao destinatário",
        delivered=True,
        expected_delivery=None,
    )
    mock_api_client.async_get_packages.return_value = moved
    seen: list[tuple[str, str]] = []
    hass.bus.async_listen(
        "state_changed",
        lambda event: (
            seen.append(
                (
                    event.data["new_state"].attributes.get("event_type"),
                    event.data["new_state"].attributes.get("tracking_code"),
                )
            )
            if event.data["entity_id"] == EVENT_ENTITY_ID
            else None
        ),
    )
    await _refresh(hass)
    assert seen == [
        ("status_changed", IN_TRANSIT_CODE),
        ("delivered", SECOND_IN_TRANSIT_CODE),
    ]


async def test_refresh_without_changes_keeps_the_entity_silent(
    hass, setup_integration, mock_api_client, packages
):
    mock_api_client.async_get_packages.return_value = dict(packages)
    await _refresh(hass)
    assert hass.states.get(EVENT_ENTITY_ID).state == "unknown"

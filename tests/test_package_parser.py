from __future__ import annotations

from datetime import date

from custom_components.correios.data import CorreiosPackageDirection
from custom_components.correios.package_parser import parse_packages

from .conftest import (
    DELIVERED_CODE,
    IN_TRANSIT_CODE,
    SENT_CODE,
    raw_package,
)


def test_parses_every_group_keyed_by_tracking_code(packages):
    assert len(packages) == 5
    assert packages[IN_TRANSIT_CODE].direction is CorreiosPackageDirection.RECEIVED
    assert packages[SENT_CODE].direction is CorreiosPackageDirection.SENT


def test_delivery_state_comes_from_the_group(packages):
    assert packages[IN_TRANSIT_CODE].delivered is False
    assert packages[DELIVERED_CODE].delivered is True


def test_package_fields(packages):
    package = packages[IN_TRANSIT_CODE]
    assert package.status == "Objeto em transferência - por favor aguarde"
    assert package.location == "Valinhos - SP"
    assert package.category == "PACKET STANDARD IMPORTAÇÃO"
    assert package.expected_delivery == date(2026, 9, 25)
    assert package.delayed is False
    assert package.last_event_at is not None
    assert package.last_event_at.utcoffset() is not None


def test_events_carry_origin_and_destination(packages):
    first, last = packages[IN_TRANSIT_CODE].events
    assert first.location == "Valinhos - SP"
    assert first.destination == "Sao Paulo - SP"
    assert last.description == "Objeto postado"
    assert last.destination == ""


def test_missing_expected_delivery_is_none(packages):
    assert packages[SENT_CODE].expected_delivery is None


def test_delayed_flag():
    payload = {"enviadoParaVoce": {"transito": [raw_package("X1", delayed=True)]}}
    assert parse_packages(payload)["X1"].delayed is True


def test_tracking_code_is_normalised():
    payload = {"enviadoParaVoce": {"transito": [raw_package(" aa 123 456 789 br ")]}}
    assert list(parse_packages(payload)) == ["AA123456789BR"]


def test_malformed_payload_yields_no_packages():
    assert parse_packages({}) == {}
    assert parse_packages({"enviadoParaVoce": "nope"}) == {}
    assert parse_packages({"enviadoParaVoce": {"transito": "nope"}}) == {}
    assert parse_packages({"enviadoParaVoce": {"transito": ["nope", {}]}}) == {}


def test_malformed_timestamp_is_none():
    broken = raw_package("X1")
    broken["data_evento"] = {"date": "yesterday"}
    payload = {"enviadoParaVoce": {"transito": [broken]}}
    assert parse_packages(payload)["X1"].last_event_at is None


def test_unknown_time_zone_falls_back_to_sao_paulo():
    odd = raw_package("X1")
    odd["data_evento"]["timezone"] = "Nowhere/Land"
    payload = {"enviadoParaVoce": {"transito": [odd]}}
    parsed = parse_packages(payload)["X1"].last_event_at
    assert parsed is not None
    assert parsed.utcoffset() is not None

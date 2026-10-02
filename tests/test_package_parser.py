from __future__ import annotations

from datetime import date

from custom_components.correios.data import CorreiosPackageDirection
from custom_components.correios.package_parser import parse_packages, parse_page_counts

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
    assert first.unit == "Unidade de Logística Integrada"
    assert first.location == "Valinhos - SP"
    assert first.destination_unit == "Unidade de Tratamento"
    assert first.destination == "Sao Paulo - SP"
    assert last.description == "Objeto postado"
    assert last.destination_unit == ""
    assert last.destination == ""


def test_package_route_comes_from_the_latest_event(packages):
    package = packages[IN_TRANSIT_CODE]
    assert package.unit == "Unidade de Logística Integrada"
    assert package.destination_unit == "Unidade de Tratamento"
    assert package.destination == "Sao Paulo - SP"


def test_package_without_events_has_no_route():
    raw = raw_package("X1")
    raw["objeto"]["eventos"] = []
    package = parse_packages({"enviadoParaVoce": {"transito": [raw]}})["X1"]
    assert package.unit == ""
    assert package.destination_unit == ""
    assert package.destination == ""


def test_unit_name_joins_kind_and_name():
    raw = raw_package("X1")
    raw["objeto"]["eventos"][0]["unidade"] = {
        "nome": "CHINA",
        "tipo": "País",
        "endereco": {"cidade": None, "uf": None},
    }
    event = parse_packages({"enviadoParaVoce": {"transito": [raw]}})["X1"].events[0]
    assert event.unit == "País, CHINA"
    assert event.location == ""


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


def test_page_counts_per_direction():
    payload = {
        "paginacao": {
            "enviadoParaVoce": {"pagina": 1, "totalPaginas": 7},
            "enviadoPorVoce": {"pagina": 1, "totalPaginas": 1},
        }
    }
    assert parse_page_counts(payload) == {
        CorreiosPackageDirection.RECEIVED: 7,
        CorreiosPackageDirection.SENT: 1,
    }


def test_page_counts_ignore_missing_or_malformed_pagination():
    payload = {
        "paginacao": {
            "enviadoParaVoce": {"totalPaginas": "7"},
            "enviadoPorVoce": {"totalPaginas": True},
        }
    }
    assert parse_page_counts(payload) == {}
    assert parse_page_counts({}) == {}

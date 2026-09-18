"""Converte o payload cru de rastreamento dos Correios em pacotes do domínio."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import TYPE_CHECKING

from homeassistant.util import dt as dt_util

from .data import (
    CorreiosPackage,
    CorreiosPackageDirection,
    CorreiosPackageEvent,
)

if TYPE_CHECKING:
    from .data import CorreiosPackages, JsonObject, JsonValue

DEFAULT_TIME_ZONE = "America/Sao_Paulo"

_DIRECTION_KEYS: tuple[tuple[str, CorreiosPackageDirection], ...] = (
    ("enviadoParaVoce", CorreiosPackageDirection.RECEIVED),
    ("enviadoPorVoce", CorreiosPackageDirection.SENT),
)
_DELIVERY_STATE_KEYS: tuple[tuple[str, bool], ...] = (
    ("transito", False),
    ("entregue", True),
)


def parse_packages(payload: JsonObject) -> CorreiosPackages:
    """Monta todos os pacotes do payload, por código de rastreamento."""
    packages: CorreiosPackages = {}
    for direction_key, direction in _DIRECTION_KEYS:
        groups = _mapping(payload.get(direction_key))
        for state_key, delivered in _DELIVERY_STATE_KEYS:
            for raw_package in _mappings(groups.get(state_key)):
                package = _parse_package(raw_package, direction, delivered=delivered)
                if package.tracking_code:
                    packages[package.tracking_code] = package
    return packages


def _parse_package(
    raw_package: JsonObject,
    direction: CorreiosPackageDirection,
    *,
    delivered: bool,
) -> CorreiosPackage:
    tracked_object = _mapping(raw_package.get("objeto"))
    postal_type = _mapping(tracked_object.get("tipoPostal"))
    return CorreiosPackage(
        tracking_code=_tracking_code(_text(raw_package.get("cod_objeto"))),
        direction=direction,
        delivered=delivered,
        delayed=tracked_object.get("atrasado") is True,
        status=_text(raw_package.get("descricao")),
        status_detail=_text(raw_package.get("detalhe")),
        location=_location(
            _text(raw_package.get("cidade")), _text(raw_package.get("uf"))
        ),
        category=_text(postal_type.get("categoria")),
        expected_delivery=_parse_expected_delivery(
            _text(raw_package.get("data_prevista"))
        ),
        last_event_at=_parse_timestamp(raw_package.get("data_evento")),
        events=tuple(
            _parse_event(raw_event)
            for raw_event in _mappings(tracked_object.get("eventos"))
        ),
    )


def _tracking_code(displayed_code: str) -> str:
    """Desfaz o agrupamento de dígitos que o site aplica para exibição."""
    return "".join(displayed_code.split()).upper()


def _parse_event(raw_event: JsonObject) -> CorreiosPackageEvent:
    return CorreiosPackageEvent(
        code=_text(raw_event.get("codigo")),
        description=_text(raw_event.get("descricao")),
        detail=_text(raw_event.get("detalhe")),
        occurred_at=_parse_timestamp(raw_event.get("dtHrCriado")),
        location=_unit_location(raw_event.get("unidade")),
        destination=_unit_location(raw_event.get("unidadeDestino")),
    )


def _unit_location(raw_unit: JsonValue) -> str:
    address = _mapping(_mapping(raw_unit).get("endereco"))
    return _location(_text(address.get("cidade")), _text(address.get("uf")))


def _location(city: str, state: str) -> str:
    return " - ".join(part for part in (city.strip(), state.strip()) if part)


def _parse_expected_delivery(value: str) -> date | None:
    try:
        return datetime.strptime(value.strip(), "%d/%m/%Y").date()  # noqa: DTZ007 -- uma data de calendário não tem fuso horário
    except ValueError:
        return None


def _parse_timestamp(raw_timestamp: JsonValue) -> datetime | None:
    timestamp = _mapping(raw_timestamp)
    try:
        naive = datetime.fromisoformat(_text(timestamp.get("date")))
    except ValueError:
        return None
    time_zone = dt_util.get_time_zone(
        _text(timestamp.get("timezone")) or DEFAULT_TIME_ZONE
    ) or dt_util.get_time_zone(DEFAULT_TIME_ZONE)
    return naive.replace(tzinfo=time_zone)


def _text(value: JsonValue) -> str:
    return value if isinstance(value, str) else ""


def _mapping(value: JsonValue) -> JsonObject:
    return value if isinstance(value, Mapping) else {}


def _mappings(value: JsonValue) -> list[JsonObject]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.util import dt as dt_util

from custom_components.correios.package_parser import parse_packages

if TYPE_CHECKING:
    from collections.abc import Generator

pytest_plugins = "pytest_homeassistant_custom_component"

IN_TRANSIT_CODE = "AA111111111BR"
SECOND_IN_TRANSIT_CODE = "AA444444444BR"
DELIVERED_CODE = "BB222222222BR"
LONG_DELIVERED_CODE = "CC333333333BR"
SENT_CODE = "DD555555555BR"


def raw_timestamp(days_ago: float) -> dict:
    moment = dt_util.now(dt_util.get_time_zone("America/Sao_Paulo")) - timedelta(
        days=days_ago
    )
    return {
        "date": moment.strftime("%Y-%m-%d %H:%M:%S.000000"),
        "timezone_type": 3,
        "timezone": "America/Sao_Paulo",
    }


def raw_event(description: str, days_ago: float, *, destination: bool = False) -> dict:
    unit = {"nome": "", "endereco": {"cidade": "Valinhos", "uf": "SP"}}
    return {
        "codigo": "RO",
        "tipo": "01",
        "dtHrCriado": raw_timestamp(days_ago),
        "descricao": description,
        "detalhe": "",
        "unidade": unit,
        "unidadeDestino": {"endereco": {"cidade": "Sao Paulo", "uf": "SP"}}
        if destination
        else None,
    }


def raw_package(
    tracking_code: str,
    description: str = "Objeto em transferência - por favor aguarde",
    days_ago: float = 0.5,
    expected_delivery: str = "25/09/2026",
    *,
    delayed: bool = False,
) -> dict:
    return {
        "data_prevista": expected_delivery,
        "cod_objeto": tracking_code,
        "uf": "SP",
        "cidade": "Valinhos",
        "data_evento": raw_timestamp(days_ago),
        "codEvento": "RO",
        "tipoEvento": "01",
        "descricao": description,
        "detalhe": "",
        "objeto": {
            "codObjeto": tracking_code,
            "tipoPostal": {"sigla": "AA", "categoria": "PACKET STANDARD IMPORTAÇÃO"},
            "eventos": [
                raw_event(description, days_ago, destination=True),
                raw_event("Objeto postado", days_ago + 3),
            ],
            "atrasado": delayed,
        },
    }


def build_raw_payload() -> dict:
    return {
        "enviadoParaVoce": {
            "transito": [
                raw_package(IN_TRANSIT_CODE),
                raw_package(SECOND_IN_TRANSIT_CODE, expected_delivery="20/09/2026"),
            ],
            "entregue": [
                raw_package(
                    DELIVERED_CODE,
                    description="Objeto entregue ao destinatário",
                    days_ago=2,
                ),
                raw_package(
                    LONG_DELIVERED_CODE,
                    description="Objeto entregue ao destinatário",
                    days_ago=40,
                ),
            ],
        },
        "enviadoPorVoce": {
            "transito": [raw_package(SENT_CODE, expected_delivery="")],
            "entregue": [],
        },
    }


@pytest.fixture
def raw_payload() -> dict:
    return build_raw_payload()


@pytest.fixture
def packages(raw_payload: dict) -> dict:
    return parse_packages(raw_payload)


@pytest.fixture
def mock_api_client(packages: dict) -> Generator:
    with patch("custom_components.correios.CorreiosApiClient") as mock_class:
        instance = mock_class.return_value
        instance.async_get_packages = AsyncMock(return_value=packages)
        yield instance


@pytest.fixture
async def setup_integration(hass, mock_api_client, enable_custom_integrations):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.correios.const import DOMAIN

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="***.456.789-**",
        data={"username": "12345678909", "password": "pass"},
        unique_id="12345678909",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry

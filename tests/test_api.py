from __future__ import annotations

import json
import socket
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from yarl import URL

from custom_components.correios.api import (
    MAX_LISTING_PAGES,
    CorreiosApiClient,
    _sanitized_error_text,
)
from custom_components.correios.const import (
    LOGIN_ENTRY_URL,
    PACKAGES_URL,
    SESSION_STATUS_URL,
)
from custom_components.correios.exceptions import (
    CorreiosApiClientAuthenticationError,
    CorreiosApiClientCommunicationError,
    CorreiosApiClientError,
    CorreiosApiClientListingExpiredError,
)

from .conftest import DELIVERED_CODE, IN_TRANSIT_CODE, SENT_CODE, raw_package

CAS_LOGIN_URL = "https://cas.correios.com.br/login?service=tracking"
SERVICE_URL = "https://rastreamento.correios.com.br/core/seguranca/service.php"
LOGIN_FORM = '<input type="hidden" name="execution" value="token-123"/>'
LOGGED_IN = json.dumps({"logado": True})
LOGGED_OUT = json.dumps({"logado": False})
NOT_LOGGED_IN_LISTING = json.dumps(
    {"erro": True, "mensagem": "Usuário não está logado"}
)
LISTING_EXPIRED = json.dumps(
    {"erro": True, "codigo": "SNAPSHOT_EXPIRADO", "mensagem": "Expirou"}
)


def _listing_page(
    received_pages: int = 1, sent_pages: int = 1, **sections: list[dict]
) -> str:
    return json.dumps(
        {
            **{
                section: {"transito": packages, "entregue": []}
                for section, packages in sections.items()
            },
            "paginacao": {
                "enviadoParaVoce": {"pagina": 1, "totalPaginas": received_pages},
                "enviadoPorVoce": {"pagina": 1, "totalPaginas": sent_pages},
            },
        }
    )


def _response(body="", status=200, url=PACKAGES_URL):
    response = MagicMock()
    response.status = status
    response.url = URL(url)
    response.text = AsyncMock(return_value=body)
    if status >= 400:
        response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=status
        )
    return response


class FakeSession:
    def __init__(self, *outcomes):
        self._outcomes = list(outcomes)
        self.calls: list[dict] = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self._outcomes.pop(0)

        @asynccontextmanager
        async def _context():
            if isinstance(outcome, BaseException):
                raise outcome
            yield outcome

        return _context()


def _client(session) -> CorreiosApiClient:
    return CorreiosApiClient(
        username="12345678909", password=",p@ss&w=rd%", session=session
    )


def test_exception_hierarchy():
    assert issubclass(CorreiosApiClientCommunicationError, CorreiosApiClientError)
    assert issubclass(CorreiosApiClientAuthenticationError, CorreiosApiClientError)
    assert issubclass(CorreiosApiClientError, Exception)


async def test_get_packages_with_live_session(raw_payload):
    session = FakeSession(_response(json.dumps(raw_payload)))
    packages = await _client(session).async_get_packages()
    assert IN_TRANSIT_CODE in packages
    assert session.calls[0]["url"] == PACKAGES_URL
    assert session.calls[0]["params"] == {"cpfcnpj": ""}


@pytest.mark.parametrize("anonymous_listing", [NOT_LOGGED_IN_LISTING, "[]"])
async def test_get_packages_logs_in_when_the_session_expired(
    raw_payload, anonymous_listing
):
    session = FakeSession(
        _response(anonymous_listing),
        _response(LOGGED_OUT, url=SESSION_STATUS_URL),
        _response(LOGIN_FORM, url=CAS_LOGIN_URL),
        _response("<html/>", url=SERVICE_URL),
        _response(LOGGED_IN, url=SESSION_STATUS_URL),
        _response(json.dumps(raw_payload)),
    )
    packages = await _client(session).async_get_packages()
    assert IN_TRANSIT_CODE in packages
    assert [call["url"] for call in session.calls] == [
        PACKAGES_URL,
        SESSION_STATUS_URL,
        LOGIN_ENTRY_URL,
        CAS_LOGIN_URL,
        SESSION_STATUS_URL,
        PACKAGES_URL,
    ]


async def test_login_posts_the_credentials_untouched():
    session = FakeSession(
        _response(LOGIN_FORM, url=CAS_LOGIN_URL),
        _response("<html/>", url=SERVICE_URL),
        _response(LOGGED_IN, url=SESSION_STATUS_URL),
    )
    await _client(session).async_authenticate()
    login_call = session.calls[1]
    assert login_call["method"] == "post"
    assert login_call["data"] == {
        "username": "12345678909",
        "password": ",p@ss&w=rd%",
        "execution": "token-123",
        "_eventId": "submit",
        "geolocation": "",
    }


async def test_empty_list_with_live_session_means_no_packages():
    session = FakeSession(
        _response("[]"),
        _response(LOGGED_IN, url=SESSION_STATUS_URL),
    )
    assert await _client(session).async_get_packages() == {}


async def test_empty_list_after_a_fresh_login_means_no_packages():
    session = FakeSession(
        _response("[]"),
        _response(LOGGED_OUT, url=SESSION_STATUS_URL),
        _response("<html/>", url=SERVICE_URL),
        _response(LOGGED_IN, url=SESSION_STATUS_URL),
        _response("[]"),
    )
    assert await _client(session).async_get_packages() == {}


async def test_single_sign_on_still_valid_skips_the_form():
    session = FakeSession(
        _response("<html/>", url=SERVICE_URL),
        _response(LOGGED_IN, url=SESSION_STATUS_URL),
    )
    await _client(session).async_authenticate()
    assert len(session.calls) == 2


async def test_rejected_credentials_raise_authentication_error():
    session = FakeSession(
        _response(LOGIN_FORM, url=CAS_LOGIN_URL),
        _response(LOGIN_FORM, status=401, url=CAS_LOGIN_URL),
    )
    with pytest.raises(CorreiosApiClientAuthenticationError):
        await _client(session).async_authenticate()


async def test_captcha_demand_raises_api_error():
    form = LOGIN_FORM + '<input type="hidden" id="recaptchaEnabled" value="true" />'
    session = FakeSession(_response(form, url=CAS_LOGIN_URL))
    with pytest.raises(CorreiosApiClientError, match="captcha"):
        await _client(session).async_authenticate()


async def test_unrecognised_login_form_raises_api_error():
    session = FakeSession(_response("<html>maintenance</html>", url=CAS_LOGIN_URL))
    with pytest.raises(CorreiosApiClientError, match="login form"):
        await _client(session).async_authenticate()


async def test_login_not_landing_on_the_tracking_site_raises_api_error():
    session = FakeSession(
        _response(LOGIN_FORM, url=CAS_LOGIN_URL),
        _response("<html/>", url=CAS_LOGIN_URL),
    )
    with pytest.raises(CorreiosApiClientError, match="hand the session over"):
        await _client(session).async_authenticate()


async def test_login_without_session_raises_api_error():
    session = FakeSession(
        _response("<html/>", url=SERVICE_URL),
        _response(LOGGED_OUT, url=SESSION_STATUS_URL),
    )
    with pytest.raises(CorreiosApiClientError, match="did not open a session"):
        await _client(session).async_authenticate()


async def test_error_payload_with_live_session_raises_api_error():
    body = json.dumps({"erro": True, "mensagem": "Sistema indisponível"})
    session = FakeSession(
        _response(body),
        _response(LOGGED_IN, url=SESSION_STATUS_URL),
    )
    with pytest.raises(CorreiosApiClientError, match="Sistema indisponível"):
        await _client(session).async_get_packages()


async def test_error_payload_after_a_fresh_login_raises_api_error():
    session = FakeSession(
        _response(NOT_LOGGED_IN_LISTING),
        _response(LOGGED_OUT, url=SESSION_STATUS_URL),
        _response("<html/>", url=SERVICE_URL),
        _response(LOGGED_IN, url=SESSION_STATUS_URL),
        _response(NOT_LOGGED_IN_LISTING),
    )
    with pytest.raises(CorreiosApiClientError, match="não está logado"):
        await _client(session).async_get_packages()


async def test_get_packages_reads_every_page_of_each_direction():
    session = FakeSession(
        _response(
            _listing_page(
                received_pages=2,
                sent_pages=2,
                enviadoParaVoce=[raw_package(IN_TRANSIT_CODE)],
            )
        ),
        _response(_listing_page(enviadoParaVoce=[raw_package(DELIVERED_CODE)])),
        _response(_listing_page(enviadoPorVoce=[raw_package(SENT_CODE)])),
    )
    packages = await _client(session).async_get_packages()
    assert set(packages) == {IN_TRANSIT_CODE, DELIVERED_CODE, SENT_CODE}
    assert [call["params"] for call in session.calls] == [
        {"cpfcnpj": ""},
        {"tipo": "D", "pagina": "2"},
        {"tipo": "R", "pagina": "2"},
    ]


async def test_get_packages_stops_at_the_page_limit():
    pages = [_response(_listing_page()) for _ in range(MAX_LISTING_PAGES - 1)]
    session = FakeSession(
        _response(_listing_page(received_pages=MAX_LISTING_PAGES + 10)), *pages
    )
    await _client(session).async_get_packages()
    assert len(session.calls) == MAX_LISTING_PAGES


async def test_expired_listing_is_fetched_again():
    session = FakeSession(
        _response(_listing_page(received_pages=2)),
        _response(LISTING_EXPIRED),
        _response(
            _listing_page(
                received_pages=2, enviadoParaVoce=[raw_package(IN_TRANSIT_CODE)]
            )
        ),
        _response(_listing_page(enviadoParaVoce=[raw_package(DELIVERED_CODE)])),
    )
    packages = await _client(session).async_get_packages()
    assert set(packages) == {IN_TRANSIT_CODE, DELIVERED_CODE}


async def test_listing_expiring_twice_raises_api_error():
    session = FakeSession(
        _response(_listing_page(received_pages=2)),
        _response(LISTING_EXPIRED),
        _response(_listing_page(received_pages=2)),
        _response(LISTING_EXPIRED),
    )
    with pytest.raises(CorreiosApiClientListingExpiredError):
        await _client(session).async_get_packages()


@pytest.mark.parametrize(
    ("page_body", "message"),
    [
        ("[]", "page 2 is not a listing"),
        (json.dumps({"erro": True, "mensagem": "Falhou"}), "Falhou"),
    ],
)
async def test_unusable_next_page_raises_api_error(page_body, message):
    session = FakeSession(
        _response(_listing_page(received_pages=2)),
        _response(page_body),
    )
    with pytest.raises(CorreiosApiClientError, match=message):
        await _client(session).async_get_packages()


async def test_non_json_body_raises_api_error():
    with pytest.raises(CorreiosApiClientError, match="not JSON"):
        await _client(FakeSession(_response("<html/>"))).async_get_packages()


async def test_http_error_raises_communication_error():
    session = FakeSession(_response(status=503))
    with pytest.raises(CorreiosApiClientCommunicationError, match="Error fetching"):
        await _client(session).async_get_packages()


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        (TimeoutError("timed out"), "Timeout"),
        (aiohttp.ClientError("refused"), "Error fetching"),
        (socket.gaierror("dns"), "Error fetching"),
    ],
)
async def test_transport_failures_raise_communication_error(failure, message):
    with pytest.raises(CorreiosApiClientCommunicationError, match=message):
        await _client(FakeSession(failure)).async_get_packages()


async def test_error_message_hides_the_single_sign_on_ticket():
    failure = aiohttp.ClientError(f"GET {SERVICE_URL}?ticket=ST-secret failed")
    with pytest.raises(CorreiosApiClientCommunicationError) as excinfo:
        await _client(FakeSession(failure)).async_get_packages()
    assert "ST-secret" not in str(excinfo.value)
    assert "<redacted>" in str(excinfo.value)


def test_sanitized_error_text_keeps_text_without_a_query_string():
    assert _sanitized_error_text(TimeoutError("timed out")) == "timed out"

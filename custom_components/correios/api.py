"""Cliente da API dos Correios."""

from __future__ import annotations

import asyncio
import json
import re
import socket
from collections.abc import Mapping
from http import HTTPStatus
from typing import TYPE_CHECKING

import aiohttp
from yarl import URL

from .const import (
    LOGIN_ENTRY_URL,
    PACKAGES_URL,
    SESSION_STATUS_URL,
    TRACKING_BASE_URL,
    TRACKING_PAGE_URL,
)
from .data import CorreiosHttpResponse
from .exceptions import (
    CorreiosApiClientAuthenticationError,
    CorreiosApiClientCommunicationError,
    CorreiosApiClientError,
)
from .package_parser import parse_packages

if TYPE_CHECKING:
    from .data import CorreiosPackages, JsonValue

REQUEST_TIMEOUT_SECONDS = 60
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

_TRACKING_HOST = URL(TRACKING_BASE_URL).host
_URL_QUERY_STRING = re.compile(r"\?\S*")
_LOGIN_EXECUTION_TOKEN = re.compile(r'name="execution"\s+value="([^"]+)"')
_LOGIN_CAPTCHA_ENABLED = re.compile(r'id="recaptchaEnabled"\s+value="true"')


def _sanitized_error_text(exception: BaseException) -> str:
    """
    Remove as query strings de URL do texto de erro antes que ele chegue ao log.

    O login único entrega a sessão por meio de um ticket de uso único na query
    string, e as bibliotecas de cliente HTTP citam a URL da requisição nas
    mensagens de exceção, que o Home Assistant grava no log a cada atualização
    que falha.
    """
    return _URL_QUERY_STRING.sub("?<redacted>", str(exception))


class CorreiosApiClient:
    """Cliente da área de rastreamento de pacotes do site dos Correios."""

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """
        Inicializa.

        O site autentica por cookies, então ``session`` precisa ter o seu
        próprio cookie jar em vez de compartilhar o do Home Assistant.
        """
        self._username = username
        self._password = password
        self._session = session

    async def async_authenticate(self) -> None:
        """Faz login e comprova que o site aceitou a sessão."""
        await self._async_log_in()
        if not await self._async_is_logged_in():
            msg = "Failed to log in: the website did not open a session"
            raise CorreiosApiClientError(msg)

    async def async_get_packages(self) -> CorreiosPackages:
        """Retorna todos os pacotes vinculados à conta, por código de rastreamento."""
        payload = await self._async_fetch_packages()
        if not isinstance(payload, Mapping):
            # A listagem responde a uma requisição anônima com uma lista vazia
            # em vez de um erro, então uma sessão expirada parece "nenhum
            # pacote" até que o status da sessão diga o contrário.
            if await self._async_is_logged_in():
                return {}
            await self.async_authenticate()
            payload = await self._async_fetch_packages()
        if not isinstance(payload, Mapping):
            return {}
        if payload.get("erro") is True:
            msg = f"Failed to list packages: {payload.get('mensagem')}"
            raise CorreiosApiClientError(msg)
        return parse_packages(payload)

    async def _async_fetch_packages(self) -> JsonValue:
        response = await self._async_send("get", PACKAGES_URL, query={"cpfcnpj": ""})
        return _decode_json(response)

    async def _async_is_logged_in(self) -> bool:
        payload = _decode_json(await self._async_send("get", SESSION_STATUS_URL))
        return isinstance(payload, Mapping) and payload.get("logado") is True

    async def _async_log_in(self) -> None:
        login_page = await self._async_send("get", LOGIN_ENTRY_URL)
        if login_page.url.host == _TRACKING_HOST:
            return
        if _LOGIN_CAPTCHA_ENABLED.search(login_page.body):
            msg = "Failed to log in: the website is demanding a captcha"
            raise CorreiosApiClientError(msg)
        execution_token = _LOGIN_EXECUTION_TOKEN.search(login_page.body)
        if execution_token is None:
            msg = "Failed to log in: the login form was not recognised"
            raise CorreiosApiClientError(msg)

        landing_page = await self._async_send(
            "post",
            str(login_page.url),
            form={
                "username": self._username,
                "password": self._password,
                "execution": execution_token.group(1),
                "_eventId": "submit",
                "geolocation": "",
            },
            accepted_statuses=frozenset({HTTPStatus.UNAUTHORIZED}),
        )
        if landing_page.status == HTTPStatus.UNAUTHORIZED:
            msg = "Invalid credentials"
            raise CorreiosApiClientAuthenticationError(msg)
        if landing_page.url.host != _TRACKING_HOST:
            msg = "Failed to log in: the website did not hand the session over"
            raise CorreiosApiClientError(msg)

    async def _async_send(
        self,
        method: str,
        url: str,
        query: Mapping[str, str] | None = None,
        form: Mapping[str, str] | None = None,
        accepted_statuses: frozenset[int] = frozenset(),
    ) -> CorreiosHttpResponse:
        """Executa uma requisição HTTP, seguindo redirecionamentos, e lê o corpo."""
        try:
            async with (
                asyncio.timeout(REQUEST_TIMEOUT_SECONDS),
                self._session.request(
                    method=method,
                    url=url,
                    params=query,
                    data=form,
                    headers={"User-Agent": USER_AGENT, "Referer": TRACKING_PAGE_URL},
                ) as response,
            ):
                if response.status not in accepted_statuses:
                    response.raise_for_status()
                return CorreiosHttpResponse(
                    status=response.status,
                    url=response.url,
                    body=await response.text(),
                )
        except TimeoutError as exception:
            detail = _sanitized_error_text(exception)
            msg = f"Timeout error fetching information - {detail}"
            raise CorreiosApiClientCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            detail = _sanitized_error_text(exception)
            msg = f"Error fetching information - {detail}"
            raise CorreiosApiClientCommunicationError(msg) from exception


def _decode_json(response: CorreiosHttpResponse) -> JsonValue:
    try:
        decoded: JsonValue = json.loads(response.body)
    except ValueError as exception:
        msg = "Failed to process the API response: the body is not JSON"
        raise CorreiosApiClientError(msg) from exception
    return decoded

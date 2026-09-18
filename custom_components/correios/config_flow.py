"""Config flow dos correios."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.util import slugify

from .api import CorreiosApiClient
from .const import CPF_LENGTH, DOMAIN, LOGGER
from .exceptions import (
    CorreiosApiClientAuthenticationError,
    CorreiosApiClientCommunicationError,
    CorreiosApiClientError,
)
from .options_flow import CorreiosOptionsFlow

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .data import CorreiosConfigData, CorreiosConfigEntry


def _credentials_schema(default_username: str | None = None) -> vol.Schema:
    """Monta o schema de usuário/senha, opcionalmente já preenchido."""
    return vol.Schema(
        {
            vol.Required(
                CONF_USERNAME,
                default=default_username
                if default_username is not None
                else vol.UNDEFINED,
            ): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT),
            ),
            vol.Required(CONF_PASSWORD): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD),
            ),
        },
    )


def _normalized(user_input: CorreiosConfigData) -> CorreiosConfigData:
    """Remove os espaços que um usuário colado costuma trazer."""
    return {
        "username": user_input["username"].strip(),
        "password": user_input["password"],
    }


def _account_title(username: str) -> str:
    """Nomeia a entry de acordo com a conta, sem expor um CPF inteiro."""
    digits = username.replace(".", "").replace("-", "")
    if not digits.isdigit() or len(digits) != CPF_LENGTH:
        return username
    return f"***.{digits[3:6]}.{digits[6:9]}-**"


class CorreiosFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow dos Correios."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: CorreiosConfigEntry,  # noqa: ARG004
    ) -> CorreiosOptionsFlow:
        """Retorna o handler do options flow."""
        return CorreiosOptionsFlow()

    # O parâmetro estreitado para ``CorreiosConfigData`` é intencional: a
    # classe base do HA declara ``dict[str, Any] | None`` aqui, e trocamos a
    # conformidade estrita com o LSP por uma tipagem mais forte do user_input.
    async def async_step_user(  # type: ignore[override]
        self,
        user_input: CorreiosConfigData | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Trata o passo inicial."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input = _normalized(user_input)
            errors = await self._validate(user_input)
            if not errors:
                await self.async_set_unique_id(slugify(user_input["username"]))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=_account_title(user_input["username"]),
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_credentials_schema(
                default_username=user_input["username"] if user_input else None,
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self,
        entry_data: Mapping[str, str],  # noqa: ARG002
    ) -> config_entries.ConfigFlowResult:
        """Dispara o reauth quando a API rejeita as credenciais armazenadas."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: CorreiosConfigData | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Solicita novas credenciais ao usuário e atualiza a entry."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        existing = cast("CorreiosConfigData", entry.data)

        if user_input is not None:
            user_input = _normalized(user_input)
            errors = await self._validate(user_input)
            if not errors:
                await self.async_set_unique_id(slugify(user_input["username"]))
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=dict(user_input),
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=_credentials_schema(
                default_username=existing.get("username"),
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: CorreiosConfigData | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Permite editar as credenciais de uma entry existente."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()
        existing = cast("CorreiosConfigData", entry.data)

        if user_input is not None:
            user_input = _normalized(user_input)
            errors = await self._validate(user_input)
            if not errors:
                await self.async_set_unique_id(slugify(user_input["username"]))
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=dict(user_input),
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_credentials_schema(
                default_username=existing.get("username"),
            ),
            errors=errors,
        )

    async def _validate(
        self,
        user_input: CorreiosConfigData,
    ) -> dict[str, str]:
        """Testa as credenciais e retorna um dict de erros (vazio no sucesso)."""
        try:
            await self._test_credentials(
                username=user_input["username"],
                password=user_input["password"],
            )
        except CorreiosApiClientAuthenticationError as exception:
            LOGGER.warning("Failed to authenticate: %s", exception)
            return {"base": "auth"}
        except CorreiosApiClientCommunicationError as exception:
            LOGGER.error("Failed to connect to the API: %s", exception)
            return {"base": "connection"}
        except CorreiosApiClientError:
            LOGGER.exception("Failed to validate credentials")
            return {"base": "unknown"}
        return {}

    async def _test_credentials(self, username: str, password: str) -> None:
        """Valida as credenciais contra a API."""
        client = CorreiosApiClient(
            username=username,
            password=password,
            session=async_create_clientsession(self.hass),
        )
        await client.async_authenticate()

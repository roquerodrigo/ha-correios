"""Registro, no frontend, do card do Lovelace que acompanha a integração."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection

from .const import DOMAIN, STATIC_URL_PREFIX

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_STATIC_PATH_REGISTERED_KEY = f"{DOMAIN}_static_path_registered"
_EXTRA_MODULE_REGISTERED_KEY = f"{DOMAIN}_extra_module_registered"
_CARD_URL = f"{STATIC_URL_PREFIX}/correios-card.js"
_WWW_DIR = Path(__file__).parent / "www"
_CARD_FILE = _WWW_DIR / "correios-card.js"
_FINGERPRINT_LENGTH = 8


class CorreiosDashboardResource(TypedDict):
    """Recurso de dashboard como a coleção de recursos do Lovelace o armazena."""

    id: str
    url: str


class CorreiosCardRegistration:
    """
    Serve o card que acompanha a integração e o mantém registrado nos dashboards.

    O card é registrado como recurso de dashboard do Lovelace, e não como
    módulo extra do frontend: os módulos extras são embutidos no index.html
    apenas nas páginas servidas depois que esta integração começou o setup,
    então um dashboard aberto enquanto o Home Assistant ainda iniciava exibia
    um erro de configuração até um recarregamento manual. Os recursos de
    dashboard persistem no storage e são buscados a cada carregamento do
    dashboard, o que fecha essa janela de inicialização. O add_extra_js_url()
    permanece apenas como fallback para recursos em modo YAML, que não podem
    ser gerenciados por código.
    """

    def __init__(self, hass: HomeAssistant, version: str) -> None:
        """Inicializa o registro para uma versão do card."""
        self._hass = hass
        self._version = version

    async def async_register(self) -> None:
        """Serve os arquivos do card e garante que os dashboards os carreguem."""
        await self._async_register_static_path()
        versioned_url = await self._async_versioned_url()
        if (resources := self._storage_resources()) is None:
            self._register_extra_module(versioned_url)
        else:
            await self._async_ensure_resource(resources, versioned_url)

    async def async_remove(self) -> None:
        """Remove o recurso de dashboard do card."""
        if (resources := self._storage_resources()) is None:
            return
        if not resources.loaded:
            await resources.async_load()
        for item in _resource_items(resources):
            if item["url"].startswith(_CARD_URL):
                await resources.async_delete_item(item["id"])

    async def _async_versioned_url(self) -> str:
        """
        Retorna a URL do card com um cache-buster que acompanha o conteúdo.

        O card é servido com cabeçalhos de cache de longa duração, e a versão
        da integração sozinha não muda quando o card é editado entre releases,
        o que deixaria os navegadores com o arquivo antigo.
        """
        fingerprint = await self._hass.async_add_executor_job(_card_fingerprint)
        return f"{_CARD_URL}?v={self._version}-{fingerprint}"

    async def _async_register_static_path(self) -> None:
        if self._hass.data.get(_STATIC_PATH_REGISTERED_KEY):
            return
        await self._hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL_PREFIX, str(_WWW_DIR), cache_headers=True)]
        )
        self._hass.data[_STATIC_PATH_REGISTERED_KEY] = True

    def _register_extra_module(self, versioned_url: str) -> None:
        if self._hass.data.get(_EXTRA_MODULE_REGISTERED_KEY):
            return
        add_extra_js_url(self._hass, versioned_url)
        self._hass.data[_EXTRA_MODULE_REGISTERED_KEY] = True

    def _storage_resources(self) -> ResourceStorageCollection | None:
        if (lovelace := self._hass.data.get(LOVELACE_DATA)) is None:
            return None
        resources = lovelace.resources
        if not isinstance(resources, ResourceStorageCollection):
            return None
        return resources

    async def _async_ensure_resource(
        self, resources: ResourceStorageCollection, versioned_url: str
    ) -> None:
        if not resources.loaded:
            await resources.async_load()
        for item in _resource_items(resources):
            if not item["url"].startswith(_CARD_URL):
                continue
            if item["url"] != versioned_url:
                await resources.async_update_item(item["id"], {"url": versioned_url})
            return
        await resources.async_create_item({"res_type": "module", "url": versioned_url})


def _card_fingerprint() -> str:
    return sha256(_CARD_FILE.read_bytes()).hexdigest()[:_FINGERPRINT_LENGTH]


def _resource_items(
    resources: ResourceStorageCollection,
) -> list[CorreiosDashboardResource]:
    return [cast("CorreiosDashboardResource", item) for item in resources.async_items()]

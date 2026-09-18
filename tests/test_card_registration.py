"""Testes do registro do card do Lovelace que acompanha a integração."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL, UrlManager
from homeassistant.components.lovelace import LOVELACE_DATA
from homeassistant.loader import async_get_integration
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.correios import async_remove_entry
from custom_components.correios.card_registration import (
    CorreiosCardRegistration,
    _card_fingerprint,
)
from custom_components.correios.const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

CARD_URL = "/correios/correios-card.js"
FINGERPRINT = _card_fingerprint()


def _card_resource_urls(hass: HomeAssistant) -> list[str]:
    """Retorna as URLs dos recursos de dashboard registrados para o card."""
    resources = hass.data[LOVELACE_DATA].resources
    return [
        item["url"]
        for item in resources.async_items()
        if item["url"].startswith(CARD_URL)
    ]


async def _register(hass: HomeAssistant, version: str) -> None:
    """Configura o http e executa o registro do card."""
    assert await async_setup_component(hass, "http", {})
    await CorreiosCardRegistration(hass, version).async_register()


async def test_register_creates_dashboard_resource(hass: HomeAssistant) -> None:
    """O modo storage recebe um recurso de dashboard versionado para o card."""
    assert await async_setup_component(hass, "lovelace", {})
    await _register(hass, "1.2.3")

    assert _card_resource_urls(hass) == [f"{CARD_URL}?v=1.2.3-{FINGERPRINT}"]


async def test_register_updates_stale_resource_version(hass: HomeAssistant) -> None:
    """Um recurso existente com versão antiga é atualizado no lugar."""
    assert await async_setup_component(hass, "lovelace", {})
    await _register(hass, "1.2.3")
    await CorreiosCardRegistration(hass, "1.3.0").async_register()

    assert _card_resource_urls(hass) == [f"{CARD_URL}?v=1.3.0-{FINGERPRINT}"]


async def test_register_twice_keeps_single_resource(hass: HomeAssistant) -> None:
    """Registrar a mesma versão duas vezes não duplica o recurso."""
    assert await async_setup_component(hass, "lovelace", {})
    await _register(hass, "1.2.3")
    await CorreiosCardRegistration(hass, "1.2.3").async_register()

    assert _card_resource_urls(hass) == [f"{CARD_URL}?v=1.2.3-{FINGERPRINT}"]


async def test_register_keeps_unrelated_resources(hass: HomeAssistant) -> None:
    """Os recursos de outros cards permanecem intactos."""
    assert await async_setup_component(hass, "lovelace", {})
    resources = hass.data[LOVELACE_DATA].resources
    await resources.async_load()
    await resources.async_create_item(
        {"res_type": "module", "url": "/hacsfiles/other-card/other-card.js"}
    )

    await _register(hass, "1.2.3")

    urls = [item["url"] for item in resources.async_items()]
    assert "/hacsfiles/other-card/other-card.js" in urls


async def test_yaml_mode_falls_back_to_extra_module(hass: HomeAssistant) -> None:
    """Recursos em modo YAML recorrem ao add_extra_js_url."""
    hass.data.setdefault(DATA_EXTRA_MODULE_URL, UrlManager(lambda *_: None, []))
    assert await async_setup_component(hass, "lovelace", {"lovelace": {"mode": "yaml"}})

    await _register(hass, "1.2.3")
    await CorreiosCardRegistration(hass, "1.2.3").async_register()

    urls = [u for u in hass.data[DATA_EXTRA_MODULE_URL].urls if u.startswith(CARD_URL)]
    assert urls == [f"{CARD_URL}?v=1.2.3-{FINGERPRINT}"]


async def test_missing_lovelace_data_falls_back_to_extra_module(
    hass: HomeAssistant,
) -> None:
    """Sem os dados do lovelace, o card é registrado como módulo extra."""
    hass.data.setdefault(DATA_EXTRA_MODULE_URL, UrlManager(lambda *_: None, []))

    await _register(hass, "1.2.3")

    urls = hass.data[DATA_EXTRA_MODULE_URL].urls
    assert any(u.startswith(f"{CARD_URL}?v=") for u in urls)


async def test_remove_deletes_dashboard_resource(hass: HomeAssistant) -> None:
    """Remover o registro exclui o recurso de dashboard."""
    assert await async_setup_component(hass, "lovelace", {})
    await _register(hass, "1.2.3")

    await CorreiosCardRegistration(hass, "1.2.3").async_remove()

    assert _card_resource_urls(hass) == []


async def test_remove_without_lovelace_data_is_noop(hass: HomeAssistant) -> None:
    """Remover sem os dados do lovelace não faz nada."""
    await CorreiosCardRegistration(hass, "1.2.3").async_remove()


async def test_remove_loads_resources_before_deleting(hass: HomeAssistant) -> None:
    """Remover logo após a inicialização carrega antes a coleção de recursos."""
    assert await async_setup_component(hass, "lovelace", {})

    await CorreiosCardRegistration(hass, "1.2.3").async_remove()

    assert _card_resource_urls(hass) == []


async def test_remove_entry_drops_resource_for_last_entry(
    hass: HomeAssistant,
    enable_custom_integrations: None,
) -> None:
    """Remover a última config entry exclui o recurso de dashboard."""
    assert await async_setup_component(hass, "lovelace", {})
    await _register(hass, "1.2.3")
    await async_get_integration(hass, DOMAIN)
    entry = MockConfigEntry(domain=DOMAIN, data={})

    await async_remove_entry(hass, entry)

    assert _card_resource_urls(hass) == []


async def test_remove_entry_keeps_resource_while_entries_remain(
    hass: HomeAssistant,
) -> None:
    """O recurso permanece enquanto existir outra config entry."""
    assert await async_setup_component(hass, "lovelace", {})
    await _register(hass, "1.2.3")
    remaining_entry = MockConfigEntry(domain=DOMAIN, data={})
    remaining_entry.add_to_hass(hass)
    removed_entry = MockConfigEntry(domain=DOMAIN, data={})

    await async_remove_entry(hass, removed_entry)

    assert _card_resource_urls(hass) == [f"{CARD_URL}?v=1.2.3-{FINGERPRINT}"]


async def test_fingerprint_follows_the_card_content(
    hass: HomeAssistant, tmp_path, monkeypatch
) -> None:
    """Editar o card muda o cache-buster sem incremento de versão."""
    from custom_components.correios import card_registration

    edited_card = tmp_path / "correios-card.js"
    edited_card.write_text("console.info('edited');")
    monkeypatch.setattr(card_registration, "_CARD_FILE", edited_card)

    assert len(_card_fingerprint()) == 8
    assert _card_fingerprint() != FINGERPRINT

"""Constants for correios."""

from __future__ import annotations

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "correios"
ATTRIBUTION = "Data provided by Correios"
STATIC_URL_PREFIX = "/correios"

TRACKING_BASE_URL = "https://rastreamento.correios.com.br"
LOGIN_ENTRY_URL = f"{TRACKING_BASE_URL}/core/seguranca/entrar.php"
SESSION_STATUS_URL = f"{TRACKING_BASE_URL}/app/controle.php"
PACKAGES_URL = f"{TRACKING_BASE_URL}/app/rastrocpfcnpj.php"
TRACKING_PAGE_URL = f"{TRACKING_BASE_URL}/app/index.php"

CONF_DELIVERED_RETENTION_DAYS = "delivered_retention_days"

DEFAULT_SCAN_INTERVAL_SECONDS = 900
MIN_SCAN_INTERVAL_SECONDS = 300
DEFAULT_DELIVERED_RETENTION_DAYS = 7
MAX_DELIVERED_RETENTION_DAYS = 90

CPF_LENGTH = 11

"""DataUpdateCoordinator dos correios."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN, LOGGER
from .exceptions import (
    CorreiosApiClientAuthenticationError,
    CorreiosApiClientError,
)
from .package_changes import detect_package_changes

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant

    from .data import (
        CorreiosConfigEntry,
        CorreiosPackage,
        CorreiosPackageChange,
        CorreiosPackages,
    )

FAILURE_GRACE_PERIOD = timedelta(hours=1)


class CorreiosDataUpdateCoordinator(DataUpdateCoordinator["CorreiosPackages"]):
    """Coordinator com os pacotes que ainda vale exibir, por código de rastreamento."""

    config_entry: CorreiosConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        scan_interval: timedelta,
        delivered_retention: timedelta,
        config_entry: CorreiosConfigEntry | None = None,
    ) -> None:
        """Inicializa."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
            always_update=False,
            config_entry=config_entry,
        )
        self._delivered_retention = delivered_retention
        self._first_failure_at: datetime | None = None
        self.latest_changes: tuple[CorreiosPackageChange, ...] = ()

    async def _async_update_data(self) -> CorreiosPackages:
        """Busca os pacotes, tolerando quedas mais curtas que o período de carência."""
        try:
            packages = await self.config_entry.runtime_data.client.async_get_packages()
        except CorreiosApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except CorreiosApiClientError as exception:
            return self._handle_failure(exception)

        self._first_failure_at = None
        previous: CorreiosPackages | None = self.data
        relevant = {
            tracking_code: package
            for tracking_code, package in packages.items()
            if self._is_relevant(package)
        }
        self.latest_changes = detect_package_changes(previous, relevant)
        LOGGER.debug(
            "Fetched %d packages, %d relevant, %d changed",
            len(packages),
            len(relevant),
            len(self.latest_changes),
        )
        return relevant

    def _is_relevant(self, package: CorreiosPackage) -> bool:
        """Mantém os pacotes a caminho e os entregues dentro da retenção."""
        if not package.delivered:
            return True
        if package.last_event_at is None:
            return False
        return dt_util.utcnow() - package.last_event_at <= self._delivered_retention

    def _handle_failure(self, exception: CorreiosApiClientError) -> CorreiosPackages:
        """
        Serve os últimos dados conhecidos enquanto a queda é mais curta que a carência.

        O site de rastreamento tem quedas curtas e frequentes, e um pacote não
        deixa de existir porque uma consulta falhou: marcar todas as entidades
        como indisponíveis poluiria o histórico e quebraria automações por uma
        oscilação que se resolve sozinha na consulta seguinte. Uma queda real
        ainda aparece quando a janela se fecha, e um erro de autenticação nunca
        chega aqui.
        """
        now = dt_util.utcnow()
        if self._first_failure_at is None:
            self._first_failure_at = now

        last_known_data: CorreiosPackages | None = self.data
        if (
            last_known_data is not None
            and now - self._first_failure_at < FAILURE_GRACE_PERIOD
        ):
            LOGGER.warning(
                "Failed to fetch packages; serving the last known values: %s",
                exception,
            )
            self.latest_changes = ()
            return last_known_data

        raise UpdateFailed(exception) from exception

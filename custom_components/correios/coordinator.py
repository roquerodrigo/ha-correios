"""DataUpdateCoordinator for correios."""

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
    """Coordinator holding the packages still worth showing, by tracking code."""

    config_entry: CorreiosConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        scan_interval: timedelta,
        delivered_retention: timedelta,
        config_entry: CorreiosConfigEntry | None = None,
    ) -> None:
        """Initialize."""
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
        """Fetch the packages, tolerating outages shorter than the grace period."""
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
        """Keep packages on the way and the ones delivered within the retention."""
        if not package.delivered:
            return True
        if package.last_event_at is None:
            return False
        return dt_util.utcnow() - package.last_event_at <= self._delivered_retention

    def _handle_failure(self, exception: CorreiosApiClientError) -> CorreiosPackages:
        """
        Serve the last known data while the outage is shorter than the grace period.

        The tracking website has frequent short outages, and a package does not
        stop existing because one poll failed: marking every entity unavailable
        would pollute history and break automations for a blip that resolves
        itself on the next poll. A genuine outage still surfaces once the window
        closes, and an authentication error never reaches here.
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

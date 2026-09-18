"""Options flow dos correios."""

from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.config_entries import ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.helpers import selector

from .const import (
    CONF_DELIVERED_RETENTION_DAYS,
    DEFAULT_DELIVERED_RETENTION_DAYS,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    MAX_DELIVERED_RETENTION_DAYS,
    MIN_SCAN_INTERVAL_SECONDS,
)

if TYPE_CHECKING:
    from .data import CorreiosOptionsData


class CorreiosOptionsFlow(OptionsFlow):
    """Options flow dos Correios."""

    async def async_step_init(
        self,
        user_input: CorreiosOptionsData | None = None,
    ) -> ConfigFlowResult:
        """Gerencia as opções."""
        if user_input is not None:
            return self.async_create_entry(title="", data=dict(user_input))

        current_scan_interval: int = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            DEFAULT_SCAN_INTERVAL_SECONDS,
        )
        current_retention_days: int = self.config_entry.options.get(
            CONF_DELIVERED_RETENTION_DAYS,
            DEFAULT_DELIVERED_RETENTION_DAYS,
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current_scan_interval,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL_SECONDS,
                            step=60,
                            unit_of_measurement="s",
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                    vol.Optional(
                        CONF_DELIVERED_RETENTION_DAYS,
                        default=current_retention_days,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=MAX_DELIVERED_RETENTION_DAYS,
                            step=1,
                            unit_of_measurement="d",
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                },
            ),
        )

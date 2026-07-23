"""Kreator konfiguracji Manual Charge."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BATTERY_SOC_ENTITY,
    CONF_CHARGE_CURRENT_ENTITY,
    CONF_NOTIFICATIONS,
    DOMAIN,
    NAME,
)

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CHARGE_CURRENT_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="number")
        ),
        vol.Required(CONF_BATTERY_SOC_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        ),
        vol.Optional(CONF_NOTIFICATIONS, default=False): selector.BooleanSelector(),
    }
)


class ManuChargeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Obsługa kreatora konfiguracji."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Krok inicjujący — jedna instancja na system."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title=NAME, data=user_input)

        return self.async_show_form(step_id="user", data_schema=SCHEMA)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> ManuChargeOptionsFlow:
        """Zwraca przepływ opcji."""
        return ManuChargeOptionsFlow()


class ManuChargeOptionsFlow(OptionsFlow):
    """Zmiana konfiguracji bez ponownej instalacji."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Formularz opcji."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(SCHEMA, current),
        )

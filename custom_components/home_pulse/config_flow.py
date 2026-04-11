"""Config flow for HomePulse integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN


class HomePulseConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HomePulse.

    Only one instance of the integration is allowed.
    No credentials are required — tasks are stored locally.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="HomePulse", data={})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )

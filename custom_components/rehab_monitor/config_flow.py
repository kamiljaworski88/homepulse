"""Config flow for rehab_monitor integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import (
    CONF_HASLO,
    CONF_LOGIN,
    CONF_NOTIFY_SERVICE,
    CONF_PLACE_ID_SI,
    CONF_PLACE_ID_TERAPIA,
    DEFAULT_PLACE_ID_SI,
    DEFAULT_PLACE_ID_TERAPIA,
    DOMAIN,
)

# ── Form schema ────────────────────────────────────────────────────────────────
STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_LOGIN, default=""): str,
        vol.Optional(CONF_HASLO, default=""): str,
        vol.Required(CONF_NOTIFY_SERVICE, default="notify"): str,
        vol.Optional(CONF_PLACE_ID_TERAPIA, default=DEFAULT_PLACE_ID_TERAPIA): str,
        vol.Optional(CONF_PLACE_ID_SI, default=DEFAULT_PLACE_ID_SI): str,
    }
)


class RehabMonitorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Rehab Monitor.

    Single-instance integration: only one entry allowed.
    Login credentials are optional — leave blank if the portal does not
    require authentication (verify via DevTools before configuring).
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial (and only) configuration step."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Rehab Monitor", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            description_placeholders={
                "place_hint": (
                    "ID miejsca to wartość wysyłana w polu placeId zapytania "
                    "FreeTermsFilter — sprawdź w DevTools → Network."
                )
            },
        )

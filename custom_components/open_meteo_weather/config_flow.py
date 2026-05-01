from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_TIMEZONE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_TIMEZONE,
    DEFAULT_UPDATE_INTERVAL,
    API_URL,
)

TIMEZONES = [
    "Europe/Warsaw",
    "Europe/London",
    "Europe/Berlin",
    "Europe/Paris",
    "Europe/Kyiv",
    "UTC",
]


async def _test_connection(latitude: float, longitude: float) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                API_URL,
                params={"latitude": latitude, "longitude": longitude, "current": "temperature_2m"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                return resp.status == 200
    except aiohttp.ClientError:
        return False


class OpenMeteoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict = {}

        ha_lat = self.hass.config.latitude
        ha_lon = self.hass.config.longitude

        if user_input is not None:
            lat = user_input[CONF_LATITUDE]
            lon = user_input[CONF_LONGITUDE]

            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                errors["base"] = "invalid_coords"
            elif not await _test_connection(lat, lon):
                errors["base"] = "cannot_connect"
            else:
                unique_id = f"{lat}_{lon}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        schema = vol.Schema({
            vol.Required(CONF_NAME, default="Moja Pogoda"): str,
            vol.Required(CONF_LATITUDE, default=round(ha_lat, 4)): vol.Coerce(float),
            vol.Required(CONF_LONGITUDE, default=round(ha_lon, 4)): vol.Coerce(float),
            vol.Optional(CONF_TIMEZONE, default=DEFAULT_TIMEZONE): vol.In(TIMEZONES),
            vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                vol.Coerce(int), vol.Range(min=60, max=3600)
            ),
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

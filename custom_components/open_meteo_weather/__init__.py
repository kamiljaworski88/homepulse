from __future__ import annotations

import os
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_TIMEZONE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_TIMEZONE,
    DEFAULT_UPDATE_INTERVAL,
    CARD_URL,
    CARD_VERSION,
)
from .coordinator import OpenMeteoCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Rejestruje kartę Lovelace przy starcie HA."""
    card_path = os.path.join(os.path.dirname(__file__), "www", "open-meteo-weather-card.js")

    if os.path.isfile(card_path):
        try:
            from homeassistant.components.http import StaticPathConfig
            await hass.http.async_register_static_paths([
                StaticPathConfig(CARD_URL, card_path, False)
            ])
        except (ImportError, AttributeError):
            hass.http.register_static_path(CARD_URL, card_path, False)

        try:
            from homeassistant.components.frontend import add_extra_js_url
            add_extra_js_url(hass, f"{CARD_URL}?v={CARD_VERSION}")
        except ImportError:
            _LOGGER.warning("Nie można zarejestrować karty Lovelace automatycznie")

        await _register_lovelace_resource(hass, f"{CARD_URL}?v={CARD_VERSION}")

    return True


async def _register_lovelace_resource(hass: HomeAssistant, url: str) -> None:
    """Dodaje zasób do Lovelace w trybie storage (jeśli dostępny)."""
    try:
        from homeassistant.components.lovelace.resources import ResourceStorageCollection
        lovelace = hass.data.get("lovelace")
        if not lovelace:
            return
        resources = lovelace.get("resources")
        if not isinstance(resources, ResourceStorageCollection):
            return
        base_url = CARD_URL
        for item in resources.async_items():
            if base_url in item.get("url", ""):
                return
        await resources.async_create_item({"res_type": "module", "url": url})
        _LOGGER.info("Zarejestrowano kartę Lovelace: %s", url)
    except Exception as err:
        _LOGGER.debug("Nie udało się zarejestrować zasobu Lovelace: %s", err)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = OpenMeteoCoordinator(
        hass,
        latitude=entry.data[CONF_LATITUDE],
        longitude=entry.data[CONF_LONGITUDE],
        timezone_str=entry.data.get(CONF_TIMEZONE, DEFAULT_TIMEZONE),
        update_interval=entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()
    if not coordinator.data:
        raise ConfigEntryNotReady("Brak danych z Open-Meteo")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded

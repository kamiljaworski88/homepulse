"""HomePulse — maintenance task manager with Google Calendar sync."""
from __future__ import annotations

import logging
import os
import shutil
import uuid
from datetime import date
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .const import (
    ATTR_GOOGLE_CALENDAR_ENTITY,
    ATTR_INTERVAL_UNIT,
    ATTR_INTERVAL_VALUE,
    ATTR_TASK_ID,
    ATTR_TITLE,
    DOMAIN,
    INTERVAL_UNITS,
    PLATFORMS,
    SERVICE_ADD_TASK,
    SERVICE_COMPLETE_TASK,
    SERVICE_DELETE_TASK,
    SERVICE_UPDATE_TASK,
    SIGNAL_DELETE_TASK,
    SIGNAL_NEW_TASK,
)
from .coordinator import HomePulseCoordinator
from .google_calendar import async_create_calendar_event
from .storage import HomePulseStorage

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "home-pulse-card.js"
CARD_URL = f"/local/{CARD_FILENAME}"
LOVELACE_RESOURCES_STORAGE_KEY = "lovelace_resources"


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Copy card JS to /config/www/ and register it as a Lovelace resource."""
    await hass.async_add_executor_job(_copy_card_to_www, hass)
    await _async_ensure_lovelace_resource(hass)
    return True


def _copy_card_to_www(hass: HomeAssistant) -> None:
    """Blocking file copy — runs in executor so it doesn't block the event loop."""
    src = os.path.join(os.path.dirname(__file__), CARD_FILENAME)
    www_dir = hass.config.path("www")
    os.makedirs(www_dir, exist_ok=True)
    dst = os.path.join(www_dir, CARD_FILENAME)
    shutil.copy2(src, dst)
    _LOGGER.debug("HomePulse: copied %s → %s", src, dst)


async def _async_ensure_lovelace_resource(hass: HomeAssistant) -> None:
    """Add /local/home-pulse-card.js to Lovelace resources if not already present."""
    store = Store(hass, 1, LOVELACE_RESOURCES_STORAGE_KEY)
    data: dict[str, Any] = await store.async_load() or {"items": []}
    items: list[dict[str, Any]] = data.get("items", [])

    if any(item.get("url") == CARD_URL for item in items):
        return  # Already registered

    items.append({"id": str(uuid.uuid4()), "type": "module", "url": CARD_URL})
    data["items"] = items
    await store.async_save(data)
    _LOGGER.info(
        "HomePulse: registered Lovelace resource %s — do Ctrl+Shift+R in browser.",
        CARD_URL,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HomePulse from a config entry."""
    storage = HomePulseStorage(hass)
    await storage.async_load()

    coordinator = HomePulseCoordinator(hass, storage)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "storage": storage,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # ------------------------------------------------------------------ #
    # Service: home_pulse.complete_task                                    #
    # ------------------------------------------------------------------ #
    async def handle_complete_task(call: ServiceCall) -> None:
        task_id: str = call.data[ATTR_TASK_ID]
        task = storage.get_task(task_id)
        if not task:
            _LOGGER.error("complete_task: task '%s' not found", task_id)
            return

        today = date.today().isoformat()
        await storage.async_update_task(task_id, last_performed=today)

        if task.get("google_calendar_entity"):
            next_due = HomePulseStorage.calculate_next_due(
                today, task["interval_value"], task["interval_unit"]
            )
            await async_create_calendar_event(
                hass,
                task["google_calendar_entity"],
                task["title"],
                next_due,
            )

        await coordinator.async_request_refresh()

    # ------------------------------------------------------------------ #
    # Service: home_pulse.add_task                                         #
    # ------------------------------------------------------------------ #
    async def handle_add_task(call: ServiceCall) -> None:
        title: str = call.data[ATTR_TITLE]
        interval_value: int = call.data[ATTR_INTERVAL_VALUE]
        interval_unit: str = call.data[ATTR_INTERVAL_UNIT]
        google_calendar_entity: str = call.data.get(ATTR_GOOGLE_CALENDAR_ENTITY, "")

        task = await storage.async_add_task(
            title, interval_value, interval_unit, google_calendar_entity
        )

        if google_calendar_entity:
            next_due = HomePulseStorage.calculate_next_due(
                task["last_performed"], interval_value, interval_unit
            )
            await async_create_calendar_event(hass, google_calendar_entity, title, next_due)

        await coordinator.async_request_refresh()
        async_dispatcher_send(hass, SIGNAL_NEW_TASK, task)

    # ------------------------------------------------------------------ #
    # Service: home_pulse.update_task                                      #
    # ------------------------------------------------------------------ #
    async def handle_update_task(call: ServiceCall) -> None:
        task_id: str = call.data[ATTR_TASK_ID]
        if not storage.get_task(task_id):
            _LOGGER.error("update_task: task '%s' not found", task_id)
            return
        await storage.async_update_task(
            task_id,
            title=call.data[ATTR_TITLE],
            interval_value=call.data[ATTR_INTERVAL_VALUE],
            interval_unit=call.data[ATTR_INTERVAL_UNIT],
            google_calendar_entity=call.data.get(ATTR_GOOGLE_CALENDAR_ENTITY, ""),
        )
        await coordinator.async_request_refresh()

    # ------------------------------------------------------------------ #
    # Service: home_pulse.delete_task                                      #
    # ------------------------------------------------------------------ #
    async def handle_delete_task(call: ServiceCall) -> None:
        task_id: str = call.data[ATTR_TASK_ID]
        deleted = await storage.async_delete_task(task_id)
        if deleted:
            await coordinator.async_request_refresh()
            async_dispatcher_send(hass, SIGNAL_DELETE_TASK, task_id)

    # ------------------------------------------------------------------ #
    # Register services                                                    #
    # ------------------------------------------------------------------ #
    hass.services.async_register(
        DOMAIN,
        SERVICE_COMPLETE_TASK,
        handle_complete_task,
        schema=vol.Schema({vol.Required(ATTR_TASK_ID): str}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_TASK,
        handle_add_task,
        schema=vol.Schema(
            {
                vol.Required(ATTR_TITLE): str,
                vol.Required(ATTR_INTERVAL_VALUE): vol.All(int, vol.Range(min=1)),
                vol.Required(ATTR_INTERVAL_UNIT): vol.In(INTERVAL_UNITS),
                vol.Optional(ATTR_GOOGLE_CALENDAR_ENTITY, default=""): str,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_TASK,
        handle_update_task,
        schema=vol.Schema(
            {
                vol.Required(ATTR_TASK_ID): str,
                vol.Required(ATTR_TITLE): str,
                vol.Required(ATTR_INTERVAL_VALUE): vol.All(int, vol.Range(min=1)),
                vol.Required(ATTR_INTERVAL_UNIT): vol.In(INTERVAL_UNITS),
                vol.Optional(ATTR_GOOGLE_CALENDAR_ENTITY, default=""): str,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_TASK,
        handle_delete_task,
        schema=vol.Schema({vol.Required(ATTR_TASK_ID): str}),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
        for service in (SERVICE_COMPLETE_TASK, SERVICE_ADD_TASK, SERVICE_UPDATE_TASK, SERVICE_DELETE_TASK):
            hass.services.async_remove(DOMAIN, service)
    return unloaded

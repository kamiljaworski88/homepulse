"""Platforma switch dla komponentu HomePulse."""
from __future__ import annotations

from typing import Any
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SIGNAL_DELETE_TASK, SIGNAL_NEW_TASK
from .coordinator import HomePulseCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Ustawia platformę switch z wpisu konfiguracji."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: HomePulseCoordinator = data["coordinator"]
    storage = data["storage"]

    tracked: dict[str, HomePulseTaskSwitch] = {}

    # Encje dla zadań już istniejących w storage
    tasks = storage.get_tasks()
    switches = []
    for task in tasks:
        switch = HomePulseTaskSwitch(coordinator, task)
        tracked[task["id"]] = switch
        switches.append(switch)
    async_add_entities(switches)

    @callback
    def _on_new_task(task: dict[str, Any]) -> None:
        """Tworzy nowy przełącznik, gdy zadanie zostanie dodane przez usługę."""
        task_id = task["id"]
        if task_id not in tracked:
            switch = HomePulseTaskSwitch(coordinator, task)
            tracked[task_id] = switch
            async_add_entities([switch])

    @callback
    def _on_delete_task(task_id: str) -> None:
        """Usuwa referencję, gdy zadanie zostanie usunięte."""
        tracked.pop(task_id, None)

    config_entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_NEW_TASK, _on_new_task)
    )
    config_entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DELETE_TASK, _on_delete_task)
    )

class HomePulseTaskSwitch(CoordinatorEntity, SwitchEntity):
    """Przełącznik pauzujący konkretne zadanie HomePulse."""

    def __init__(self, coordinator: HomePulseCoordinator, task: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self._task_id = task["id"]
        self._attr_name = f"Aktywność: {task['title']}"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{self._task_id}_switch"

    @property
    def is_on(self) -> bool:
        """Zwraca True, jeśli zadanie nie jest zapauzowane."""
        return self.coordinator._task_active_states.get(self._task_id, True)

    @property
    def icon(self) -> str:
        """Dynamiczna ikona w zależności od stanu."""
        return "mdi:timer-play" if self.is_on else "mdi:timer-off-outline"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Wznów zadanie."""
        self.coordinator._task_active_states[self._task_id] = True
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Zapauzuj zadanie."""
        self.coordinator._task_active_states[self._task_id] = False
        await self.coordinator.async_request_refresh()
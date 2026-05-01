"""Platforma switch dla komponentu HomePulse."""
from __future__ import annotations

from typing import Any
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HomePulseCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Ustawia platformę switch z wpisu konfiguracji."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    storage = data["storage"]

    # Tworzymy przełącznik dla każdego zadania znajdującego się w storage
    tasks = storage.get_tasks()
    async_add_entities([HomePulseTaskSwitch(coordinator, task) for task in tasks])

class HomePulseTaskSwitch(CoordinatorEntity, SwitchEntity):
    """Przełącznik pauzujący konkretne zadanie HomePulse."""

    def __init__(self, coordinator: HomePulseCoordinator, task: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self._task_id = task["id"]
        self._attr_name = f"Aktywność: {task['title']}"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{self._task_id}_switch"
        self._attr_icon = "mdi:timer-play"

    @property
    def is_on(self) -> bool:
        """Zwraca True, jeśli zadanie nie jest zapauzowane."""
        return self.coordinator._task_active_states.get(self._task_id, True)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Wznów zadanie."""
        self.coordinator._task_active_states[self._task_id] = True
        self._attr_icon = "mdi:timer-play"
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Zapauzuj zadanie."""
        self.coordinator._task_active_states[self._task_id] = False
        self._attr_icon = "mdi:timer-pause"
        await self.coordinator.async_request_refresh()
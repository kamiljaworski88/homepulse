"""Binary sensor platform for HomePulse tasks."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SIGNAL_DELETE_TASK, SIGNAL_NEW_TASK
from .coordinator import HomePulseCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors for all persisted tasks."""
    coordinator: HomePulseCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    tracked: dict[str, HomePulseBinarySensor] = {}

    # Entities for tasks already in storage
    if coordinator.data:
        sensors = []
        for task in coordinator.data:
            sensor = HomePulseBinarySensor(coordinator, task["id"])
            tracked[task["id"]] = sensor
            sensors.append(sensor)
        async_add_entities(sensors)

    @callback
    def _on_new_task(task: dict[str, Any]) -> None:
        """Create a new binary sensor entity when a task is added via service."""
        task_id = task["id"]
        if task_id not in tracked:
            sensor = HomePulseBinarySensor(coordinator, task_id)
            tracked[task_id] = sensor
            async_add_entities([sensor])

    @callback
    def _on_delete_task(task_id: str) -> None:
        """Remove the tracked reference when a task is deleted."""
        tracked.pop(task_id, None)

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_NEW_TASK, _on_new_task)
    )
    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DELETE_TASK, _on_delete_task)
    )


class HomePulseBinarySensor(CoordinatorEntity[HomePulseCoordinator], BinarySensorEntity):
    """Represents a single HomePulse maintenance task.

    State ON  → task is overdue or due today.
    State OFF → task is upcoming.
    """

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_has_entity_name = True

    def __init__(self, coordinator: HomePulseCoordinator, task_id: str) -> None:
        super().__init__(coordinator)
        self._task_id = task_id
        self._attr_unique_id = f"home_pulse_{task_id}"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _task(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None
        for task in self.coordinator.data:
            if task["id"] == self._task_id:
                return task
        return None

    # ------------------------------------------------------------------
    # BinarySensorEntity interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        task = self._task()
        return task["title"] if task else f"HomePulse {self._task_id[:8]}"

    @property
    def is_on(self) -> bool | None:
        task = self._task()
        if task is None:
            return None
        return task["is_due"]

    @property
    def available(self) -> bool:
        return self._task() is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        task = self._task()
        if not task:
            return {}
        return {
            "task_id": task["id"],
            "days_until_next": task["days_until_next"],
            "next_due_date": task["next_due_date"],
            "overdue_by_days": task["overdue_by_days"],
            "interval_value": task["interval_value"],
            "interval_unit": task["interval_unit"],
            "last_performed": task["last_performed"],
            "google_calendar_entity": task.get("google_calendar_entity", ""),
        }

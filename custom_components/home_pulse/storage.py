"""Storage management for HomePulse tasks."""
from __future__ import annotations

import calendar
import uuid
import logging
from datetime import date, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION, INTERVAL_UNIT_DAYS, INTERVAL_UNIT_WEEKS, INTERVAL_UNIT_MONTHS

_LOGGER = logging.getLogger(__name__)


class HomePulseStorage:
    """Manages persistent storage for HomePulse tasks."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._tasks: dict[str, dict[str, Any]] = {}

    async def async_load(self) -> None:
        """Load tasks from persistent storage."""
        data = await self._store.async_load()
        if data is not None:
            self._tasks = data.get("tasks", {})
        _LOGGER.debug("Loaded %d tasks from storage", len(self._tasks))

    async def async_save(self) -> None:
        """Persist tasks to storage."""
        await self._store.async_save({"tasks": self._tasks})

    def get_tasks(self) -> list[dict[str, Any]]:
        """Return all tasks as a list."""
        return list(self._tasks.values())

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Return a single task by ID."""
        return self._tasks.get(task_id)

    async def async_add_task(
        self,
        title: str,
        interval_value: int,
        interval_unit: str,
        google_calendar_entity: str,
    ) -> dict[str, Any]:
        """Create and persist a new task."""
        task_id = str(uuid.uuid4())
        task: dict[str, Any] = {
            "id": task_id,
            "title": title,
            "interval_value": interval_value,
            "interval_unit": interval_unit,
            "last_performed": date.today().isoformat(),
            "google_calendar_entity": google_calendar_entity,
            "google_event_id": None,
            "active": True,
        }
        self._tasks[task_id] = task
        await self.async_save()
        _LOGGER.debug("Added task '%s' with id %s", title, task_id)
        return task

    async def async_update_task(self, task_id: str, **kwargs: Any) -> dict[str, Any] | None:
        """Update fields on an existing task."""
        if task_id not in self._tasks:
            _LOGGER.warning("Cannot update: task %s not found", task_id)
            return None
        self._tasks[task_id].update(kwargs)
        await self.async_save()
        return self._tasks[task_id]

    async def async_delete_task(self, task_id: str) -> bool:
        """Delete a task by ID. Returns True if deleted."""
        if task_id not in self._tasks:
            _LOGGER.warning("Cannot delete: task %s not found", task_id)
            return False
        del self._tasks[task_id]
        await self.async_save()
        _LOGGER.debug("Deleted task %s", task_id)
        return True

    @staticmethod
    def calculate_next_due(last_performed: str, interval_value: int, interval_unit: str) -> date:
        """Calculate the next due date from last_performed + interval."""
        last = date.fromisoformat(last_performed)

        if interval_unit == INTERVAL_UNIT_DAYS:
            return last + timedelta(days=interval_value)

        if interval_unit == INTERVAL_UNIT_WEEKS:
            return last + timedelta(weeks=interval_value)

        if interval_unit == INTERVAL_UNIT_MONTHS:
            month = last.month - 1 + interval_value
            year = last.year + month // 12
            month = month % 12 + 1
            day = min(last.day, calendar.monthrange(year, month)[1])
            return date(year, month, day)

        # Fallback
        return last + timedelta(days=interval_value)

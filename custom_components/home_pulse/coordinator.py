"""Data update coordinator for HomePulse."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .storage import HomePulseStorage

_LOGGER = logging.getLogger(__name__)


class HomePulseCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Fetches task data from storage and enriches it with computed properties."""

    def __init__(self, hass: HomeAssistant, storage: HomePulseStorage) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=30),
        )
        self._storage = storage
        self._task_active_states: dict[str, bool] = {}

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Compute derived fields for each task."""
        tasks = self._storage.get_tasks()
        today = date.today()
        enriched: list[dict[str, Any]] = []

        # Inicjalizacja stanów dla nowych zadań (domyślnie aktywne)
        for task in tasks:
            self._task_active_states.setdefault(task["id"], True)

        for task in tasks:
            # Jeśli zadanie jest zapauzowane, możemy je pominąć lub oznaczyć
            if not self._task_active_states.get(task["id"], True):
                continue

            next_due = HomePulseStorage.calculate_next_due(
                task["last_performed"],
                task["interval_value"],
                task["interval_unit"],
            )
            days_until = (next_due - today).days
            overdue_by = max(0, -days_until)

            enriched.append(
                {
                    **task,
                    "next_due_date": next_due.isoformat(),
                    "days_until_next": max(0, days_until),
                    "overdue_by_days": overdue_by,
                    "is_due": days_until <= 0,
                }
            )

        return enriched

"""Google Calendar helpers for HomePulse."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_create_calendar_event(
    hass: HomeAssistant,
    calendar_entity_id: str,
    summary: str,
    event_date: date,
) -> None:
    """Create a single calendar event using HA's built-in calendar service."""
    if not calendar_entity_id:
        return

    # Verify the calendar entity exists
    if hass.states.get(calendar_entity_id) is None:
        _LOGGER.warning(
            "Calendar entity '%s' not found — skipping event creation", calendar_entity_id
        )
        return

    start_dt = datetime(event_date.year, event_date.month, event_date.day, 9, 0, 0)
    end_dt = start_dt + timedelta(hours=1)

    try:
        await hass.services.async_call(
            "calendar",
            "create_event",
            {
                "entity_id": calendar_entity_id,
                "summary": f"[HomePulse] {summary}",
                "dtstart": start_dt.isoformat(),
                "dtend": end_dt.isoformat(),
                "description": f"Zadanie konserwacyjne HomePulse: {summary}",
            },
            blocking=True,
        )
        _LOGGER.debug(
            "Created calendar event for '%s' on %s in %s",
            summary,
            event_date,
            calendar_entity_id,
        )
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Failed to create calendar event for '%s': %s", summary, err)

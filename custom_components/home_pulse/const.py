"""Constants for the HomePulse integration."""
from __future__ import annotations

DOMAIN = "home_pulse"
STORAGE_KEY = "home_pulse"
STORAGE_VERSION = 1

PLATFORMS = ["binary_sensor"]

# Dispatcher signals
SIGNAL_NEW_TASK = f"{DOMAIN}_new_task"
SIGNAL_DELETE_TASK = f"{DOMAIN}_delete_task"

# Service names
SERVICE_COMPLETE_TASK = "complete_task"
SERVICE_ADD_TASK = "add_task"
SERVICE_DELETE_TASK = "delete_task"

# Service / task attributes
ATTR_TASK_ID = "task_id"
ATTR_TITLE = "title"
ATTR_INTERVAL_VALUE = "interval_value"
ATTR_INTERVAL_UNIT = "interval_unit"
ATTR_GOOGLE_CALENDAR_ENTITY = "google_calendar_entity"

# Interval units
INTERVAL_UNIT_DAYS = "days"
INTERVAL_UNIT_WEEKS = "weeks"
INTERVAL_UNIT_MONTHS = "months"
INTERVAL_UNITS = [INTERVAL_UNIT_DAYS, INTERVAL_UNIT_WEEKS, INTERVAL_UNIT_MONTHS]

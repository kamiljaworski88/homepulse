"""Number platform — configurable scan interval and active-hours window."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, HOUR_END, HOUR_START, SCAN_INTERVAL
from .coordinator import RehabDataUpdateCoordinator

_DEFAULT_INTERVAL = int(SCAN_INTERVAL.total_seconds() // 60)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: RehabDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        RehabScanIntervalNumber(coordinator),
        RehabHourStartNumber(coordinator),
        RehabHourEndNumber(coordinator),
        RehabVisitHourMinNumber(coordinator),
    ])


class _RehabNumberBase(RestoreEntity, NumberEntity):
    """Base class with restore logic shared by all rehab number entities."""

    _attr_mode = NumberMode.BOX
    _default_value: float = 0.0

    def __init__(self, coordinator: RehabDataUpdateCoordinator) -> None:
        self._coordinator = coordinator
        self._value: float = self._default_value

    async def async_added_to_hass(self) -> None:
        if (last := await self.async_get_last_state()) is not None:
            try:
                self._value = float(last.state)
            except (ValueError, TypeError):
                self._value = self._default_value
        self._apply(int(self._value))

    @property
    def native_value(self) -> float:
        return self._value

    async def async_set_native_value(self, value: float) -> None:
        self._value = value
        self._apply(int(value))
        self.async_write_ha_state()

    def _apply(self, value: int) -> None:
        raise NotImplementedError


class RehabScanIntervalNumber(_RehabNumberBase):
    """How often (in minutes) the coordinator polls the portal."""

    _attr_has_entity_name = True
    _attr_name = "Interwał sprawdzania"
    _attr_icon = "mdi:timer-outline"
    _attr_native_min_value = 1
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _default_value = float(_DEFAULT_INTERVAL)

    def __init__(self, coordinator: RehabDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_scan_interval"
        self.entity_id = "number.rehab_scan_interval"

    def _apply(self, value: int) -> None:
        self._coordinator.set_scan_interval(value)


class RehabHourStartNumber(_RehabNumberBase):
    """Earliest hour (inclusive) at which automatic polling is allowed."""

    _attr_has_entity_name = True
    _attr_name = "Sprawdzaj od (godz.)"
    _attr_icon = "mdi:clock-start"
    _attr_native_min_value = 0
    _attr_native_max_value = 22
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "h"
    _default_value = float(HOUR_START)

    def __init__(self, coordinator: RehabDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_hour_start"
        self.entity_id = "number.rehab_hour_start"

    def _apply(self, value: int) -> None:
        self._coordinator.set_hour_start(value)


class RehabHourEndNumber(_RehabNumberBase):
    """Latest hour (exclusive) until which automatic polling is allowed."""

    _attr_has_entity_name = True
    _attr_name = "Sprawdzaj do (godz.)"
    _attr_icon = "mdi:clock-end"
    _attr_native_min_value = 1
    _attr_native_max_value = 24
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "h"
    _default_value = float(HOUR_END)

    def __init__(self, coordinator: RehabDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_hour_end"
        self.entity_id = "number.rehab_hour_end"

    def _apply(self, value: int) -> None:
        self._coordinator.set_hour_end(value)


class RehabVisitHourMinNumber(_RehabNumberBase):
    """Minimum visit hour — slots before this hour are skipped (0 = all shown)."""

    _attr_has_entity_name = True
    _attr_name = "Wizyty od (godz.)"
    _attr_icon = "mdi:clock-check-outline"
    _attr_native_min_value = 0
    _attr_native_max_value = 23
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "h"
    _default_value = 0.0

    def __init__(self, coordinator: RehabDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_visit_hour_min"
        self.entity_id = "number.rehab_visit_hour_min"

    def _apply(self, value: int) -> None:
        self._coordinator.set_visit_hour_min(value)

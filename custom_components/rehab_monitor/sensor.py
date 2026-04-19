"""Sensor platform — reports count of free rehabilitation slots with full slot details."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COUNT, DATA_ERROR, DATA_LAST_UPDATE, DATA_TERMINY, DOMAIN
from .coordinator import RehabDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: RehabDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RehabWolneTerminySensor(coordinator)])


class RehabWolneTerminySensor(CoordinatorEntity[RehabDataUpdateCoordinator], SensorEntity):
    """Sensor that exposes the count and details of free rehabilitation slots.

    State: integer count of free slots (0 when none available or on error).

    extra_state_attributes:
      terminy            — list of slot dicts (data, godzina, rehabilitant, miejsce, slot_id)
      ostatnia_aktualizacja — ISO timestamp of last successful fetch
      blad               — error message string or null
    """

    _attr_has_entity_name = True
    _attr_name = "Wolne terminy"
    _attr_icon = "mdi:calendar-check"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "terminy"

    def __init__(self, coordinator: RehabDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_wolne_terminy"
        self.entity_id = "sensor.rehab_wolne_terminy"

    @property
    def native_value(self) -> int:
        if self.coordinator.data is None:
            return 0
        return int(self.coordinator.data.get(DATA_COUNT, 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self.coordinator.data is None:
            return {
                "terminy": [],
                "ostatnia_aktualizacja": None,
                "blad": None,
            }
        raw_slots: list[dict[str, Any]] = self.coordinator.data.get(DATA_TERMINY, [])
        # Expose slots without the internal slot_id to keep the UI clean
        public_slots = [
            {
                "data": s.get("data"),
                "godzina": s.get("godzina"),
                "rehabilitant": s.get("rehabilitant"),
                "miejsce": s.get("miejsce"),
                "slot_id": s.get("slot_id"),
            }
            for s in raw_slots
        ]
        return {
            "terminy": public_slots,
            "ostatnia_aktualizacja": self.coordinator.data.get(DATA_LAST_UPDATE),
            "blad": self.coordinator.data.get(DATA_ERROR),
        }

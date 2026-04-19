"""Binary sensor platform — ON when at least one free rehabilitation slot is available."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COUNT, DOMAIN
from .coordinator import RehabDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: RehabDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RehabDostepnoscBinarySensor(coordinator)])


class RehabDostepnoscBinarySensor(
    CoordinatorEntity[RehabDataUpdateCoordinator], BinarySensorEntity
):
    """Binary sensor: ON when sensor.rehab_wolne_terminy > 0.

    Useful as a trigger for automations and as a condition card in dashboards.
    device_class: occupancy — renders as "Wykryto" / "Czysto" in Polish UI.
    """

    _attr_has_entity_name = True
    _attr_name = "Dostępność terminów"
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(self, coordinator: RehabDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_dostepnosc"
        self.entity_id = "binary_sensor.rehab_dostepnosc"

    @property
    def is_on(self) -> bool:
        if self.coordinator.data is None:
            return False
        return int(self.coordinator.data.get(DATA_COUNT, 0)) > 0

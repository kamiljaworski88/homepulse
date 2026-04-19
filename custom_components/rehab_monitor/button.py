"""Button platform — triggers an immediate poll of the rehabilitation portal."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RehabDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: RehabDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RehabSprawdzTerazButton(coordinator)])


class RehabSprawdzTerazButton(ButtonEntity):
    """Button that forces an immediate coordinator refresh."""

    _attr_has_entity_name = True
    _attr_name = "Sprawdź teraz"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: RehabDataUpdateCoordinator) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_sprawdz_teraz"
        self.entity_id = "button.rehab_sprawdz_teraz"

    async def async_press(self) -> None:
        await self._coordinator.force_refresh()

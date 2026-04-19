"""Select platform — choose which place to monitor for free rehabilitation slots."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, MIEJSCA, MIEJSCE_TERAPIA
from .coordinator import RehabDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: RehabDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RehabMiejsceSelect(coordinator)])


class RehabMiejsceSelect(RestoreEntity, SelectEntity):
    """Select entity for choosing which rehabilitation place to monitor.

    Options: "Terapia dzieci", "SI-1-1", "Obie".
    When "Obie" is selected the coordinator polls both places in each cycle.
    State is preserved across restarts via RestoreEntity.
    """

    _attr_has_entity_name = True
    _attr_name = "Szukaj miejsca"
    _attr_options = MIEJSCA
    _attr_icon = "mdi:map-marker-multiple"

    def __init__(self, coordinator: RehabDataUpdateCoordinator) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_miejsce"
        self._current_option: str = MIEJSCE_TERAPIA
        self.entity_id = "select.rehab_miejsce"

    async def async_added_to_hass(self) -> None:
        """Restore the last selected option after HA restart."""
        if (last := await self.async_get_last_state()) is not None:
            if last.state in MIEJSCA:
                self._current_option = last.state
                self._coordinator.set_miejsce(self._current_option)

    @property
    def current_option(self) -> str:
        return self._current_option

    async def async_select_option(self, option: str) -> None:
        self._current_option = option
        self._coordinator.set_miejsce(option)
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()

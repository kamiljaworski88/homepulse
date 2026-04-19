"""Switch platform — enables / disables the rehabilitation monitor polling."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import RehabDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: RehabDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RehabMonitorSwitch(coordinator)])


class RehabMonitorSwitch(RestoreEntity, SwitchEntity):
    """Switch that enables/disables HTTP polling.

    When OFF no requests are sent to the portal; the coordinator returns
    the last known slot count without making any network calls.
    """

    _attr_has_entity_name = True
    _attr_name = "Monitorowanie terminów"
    _attr_icon = "mdi:hospital-box"

    def __init__(self, coordinator: RehabDataUpdateCoordinator) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_monitor_active"
        self._is_on: bool = True
        self.entity_id = "switch.rehab_monitor_active"

    async def async_added_to_hass(self) -> None:
        """Restore the last state after HA restart."""
        if (last := await self.async_get_last_state()) is not None:
            self._is_on = last.state == "on"
            self._coordinator.set_monitor_active(self._is_on)

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._is_on = True
        self._coordinator.set_monitor_active(True)
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._is_on = False
        self._coordinator.set_monitor_active(False)
        self.async_write_ha_state()

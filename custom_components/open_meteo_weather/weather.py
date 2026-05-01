from __future__ import annotations

from datetime import datetime

from homeassistant.components.weather import (
    WeatherEntity,
    WeatherEntityFeature,
    Forecast,
)
from homeassistant.const import UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, CONF_NAME, WMO_LABELS, wmo_to_condition
from .coordinator import OpenMeteoCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: OpenMeteoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([OpenMeteoWeatherEntity(coordinator, entry)], True)


class OpenMeteoWeatherEntity(CoordinatorEntity, WeatherEntity):
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self, coordinator: OpenMeteoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = entry.data[CONF_NAME]
        self._attr_unique_id = f"{entry.entry_id}_weather"

    @property
    def _current(self) -> dict:
        return self.coordinator.data.get("current", {})

    @property
    def condition(self) -> str | None:
        code = self._current.get("weather_code", 0)
        is_day = int(self._current.get("is_day", 1))
        return wmo_to_condition(code, is_day)

    @property
    def native_temperature(self) -> float | None:
        return self._current.get("temperature_2m")

    @property
    def humidity(self) -> float | None:
        return self._current.get("relative_humidity_2m")

    @property
    def native_pressure(self) -> float | None:
        return self._current.get("pressure_msl")

    @property
    def native_wind_speed(self) -> float | None:
        return self._current.get("wind_speed_10m")

    @property
    def wind_bearing(self) -> float | None:
        return self._current.get("wind_direction_10m")

    @property
    def extra_state_attributes(self) -> dict:
        cur = self._current
        daily = self.coordinator.data.get("daily", [])
        today = daily[0] if daily else {}

        return {
            "weather_code": cur.get("weather_code"),
            "weather_label": WMO_LABELS.get(cur.get("weather_code", 0), ""),
            "feels_like": cur.get("apparent_temperature"),
            "wind_gusts": cur.get("wind_gusts_10m"),
            "cloud_cover": cur.get("cloud_cover"),
            "surface_pressure": cur.get("surface_pressure"),
            "updated_at": cur.get("time"),
            "uv_index_max": today.get("uv_index_max"),
            "sunrise": today.get("sunrise"),
            "sunset": today.get("sunset"),
            "forecast_daily": self._build_daily(),
            "forecast_hourly": self._build_hourly(24),
        }

    def _build_daily(self) -> list[dict]:
        result = []
        for d in self.coordinator.data.get("daily", []):
            code = d.get("weather_code", 0)
            result.append({
                "datetime": d["datetime"],
                "condition": wmo_to_condition(code),
                "weather_code": code,
                "temperature": d.get("temperature_max"),
                "templow": d.get("temperature_min"),
                "precipitation": d.get("precipitation"),
                "precipitation_probability": d.get("precipitation_probability"),
                "wind_speed": d.get("wind_speed"),
                "wind_bearing": d.get("wind_bearing"),
                "uv_index_max": d.get("uv_index_max"),
                "sunrise": d.get("sunrise"),
                "sunset": d.get("sunset"),
            })
        return result

    def _build_hourly(self, limit: int = 48) -> list[dict]:
        result = []
        for h in self.coordinator.data.get("hourly", [])[:limit]:
            code = h.get("weather_code", 0)
            is_day = int(h.get("is_day", 1))
            result.append({
                "datetime": h["datetime"],
                "condition": wmo_to_condition(code, is_day),
                "weather_code": code,
                "temperature": h.get("temperature"),
                "humidity": h.get("humidity"),
                "precipitation": h.get("precipitation"),
                "precipitation_probability": h.get("precipitation_probability"),
                "wind_speed": h.get("wind_speed"),
                "wind_bearing": h.get("wind_bearing"),
                "pressure": h.get("pressure"),
            })
        return result

    async def async_forecast_daily(self) -> list[Forecast]:
        return [
            Forecast(
                datetime=d["datetime"],
                condition=d["condition"],
                native_temperature=d.get("temperature"),
                native_templow=d.get("templow"),
                precipitation=d.get("precipitation"),
                precipitation_probability=d.get("precipitation_probability"),
                native_wind_speed=d.get("wind_speed"),
                wind_bearing=d.get("wind_bearing"),
            )
            for d in self._build_daily()
        ]

    async def async_forecast_hourly(self) -> list[Forecast]:
        return [
            Forecast(
                datetime=h["datetime"],
                condition=h["condition"],
                native_temperature=h.get("temperature"),
                humidity=h.get("humidity"),
                precipitation=h.get("precipitation"),
                precipitation_probability=h.get("precipitation_probability"),
                native_wind_speed=h.get("wind_speed"),
                wind_bearing=h.get("wind_bearing"),
            )
            for h in self._build_hourly(48)
        ]

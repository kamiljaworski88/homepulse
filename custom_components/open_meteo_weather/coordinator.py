from __future__ import annotations

import logging
from datetime import timedelta, datetime, timezone

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

CURRENT_PARAMS = (
    "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,"
    "precipitation,weather_code,cloud_cover,pressure_msl,surface_pressure,"
    "wind_speed_10m,wind_direction_10m,wind_gusts_10m"
)
HOURLY_PARAMS = (
    "temperature_2m,relative_humidity_2m,apparent_temperature,"
    "precipitation_probability,precipitation,weather_code,pressure_msl,"
    "cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m,uv_index,is_day"
)
DAILY_PARAMS = (
    "weather_code,temperature_2m_max,temperature_2m_min,"
    "apparent_temperature_max,apparent_temperature_min,"
    "sunrise,sunset,daylight_duration,uv_index_max,"
    "precipitation_sum,precipitation_probability_max,"
    "wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant"
)


class OpenMeteoCoordinator(DataUpdateCoordinator):
    def __init__(
        self,
        hass: HomeAssistant,
        latitude: float,
        longitude: float,
        timezone_str: str,
        update_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        self.latitude = latitude
        self.longitude = longitude
        self.timezone_str = timezone_str

    async def _async_update_data(self) -> dict:
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone_str,
            "current": CURRENT_PARAMS,
            "hourly": HOURLY_PARAMS,
            "daily": DAILY_PARAMS,
            "forecast_days": 7,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Błąd połączenia z Open-Meteo: {err}") from err

        return self._parse(data)

    def _parse(self, raw: dict) -> dict:
        current = raw.get("current", {})
        daily = raw.get("daily", {})
        hourly = raw.get("hourly", {})

        # Prognoza dzienna
        daily_forecast = []
        times_d = daily.get("time", [])
        for i in range(len(times_d)):
            code = daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else 0
            daily_forecast.append({
                "datetime": times_d[i],
                "weather_code": code,
                "temperature_max": self._val(daily, "temperature_2m_max", i),
                "temperature_min": self._val(daily, "temperature_2m_min", i),
                "precipitation": self._val(daily, "precipitation_sum", i),
                "precipitation_probability": self._val(daily, "precipitation_probability_max", i),
                "wind_speed": self._val(daily, "wind_speed_10m_max", i),
                "wind_bearing": self._val(daily, "wind_direction_10m_dominant", i),
                "uv_index_max": self._val(daily, "uv_index_max", i),
                "sunrise": self._val(daily, "sunrise", i),
                "sunset": self._val(daily, "sunset", i),
            })

        # Prognoza godzinowa (48h)
        hourly_forecast = []
        times_h = hourly.get("time", [])
        now_ts = datetime.now(timezone.utc).timestamp()
        limit = min(len(times_h), 48)
        for i in range(limit):
            dt_str = times_h[i]
            try:
                dt_ts = datetime.fromisoformat(dt_str).timestamp()
            except ValueError:
                dt_ts = 0
            if dt_ts < now_ts - 1800:
                continue
            code = hourly.get("weather_code", [])[i] if i < len(hourly.get("weather_code", [])) else 0
            is_day = int(self._val(hourly, "is_day", i) or 1)
            hourly_forecast.append({
                "datetime": dt_str,
                "weather_code": code,
                "is_day": is_day,
                "temperature": self._val(hourly, "temperature_2m", i),
                "humidity": self._val(hourly, "relative_humidity_2m", i),
                "precipitation": self._val(hourly, "precipitation", i),
                "precipitation_probability": self._val(hourly, "precipitation_probability", i),
                "wind_speed": self._val(hourly, "wind_speed_10m", i),
                "wind_bearing": self._val(hourly, "wind_direction_10m", i),
                "pressure": self._val(hourly, "pressure_msl", i),
            })

        return {
            "current": current,
            "daily": daily_forecast,
            "hourly": hourly_forecast,
        }

    @staticmethod
    def _val(obj: dict, key: str, idx: int):
        arr = obj.get(key, [])
        return arr[idx] if idx < len(arr) else None

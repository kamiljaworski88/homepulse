from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfLength,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_NAME, WMO_LABELS
from .coordinator import OpenMeteoCoordinator


@dataclass(frozen=True)
class OpenMeteoSensorDescription(SensorEntityDescription):
    value_fn: callable = None


SENSORS: tuple[OpenMeteoSensorDescription, ...] = (
    OpenMeteoSensorDescription(
        key="temperature",
        name="Temperatura",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        value_fn=lambda d: d["current"].get("temperature_2m"),
    ),
    OpenMeteoSensorDescription(
        key="feels_like",
        name="Temperatura odczuwalna",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer-lines",
        value_fn=lambda d: d["current"].get("apparent_temperature"),
    ),
    OpenMeteoSensorDescription(
        key="humidity",
        name="Wilgotność",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-percent",
        value_fn=lambda d: d["current"].get("relative_humidity_2m"),
    ),
    OpenMeteoSensorDescription(
        key="pressure",
        name="Ciśnienie",
        native_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge",
        value_fn=lambda d: d["current"].get("pressure_msl"),
    ),
    OpenMeteoSensorDescription(
        key="wind_speed",
        name="Wiatr prędkość",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-windy",
        value_fn=lambda d: d["current"].get("wind_speed_10m"),
    ),
    OpenMeteoSensorDescription(
        key="wind_gusts",
        name="Wiatr porywy",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-windy-variant",
        value_fn=lambda d: d["current"].get("wind_gusts_10m"),
    ),
    OpenMeteoSensorDescription(
        key="wind_bearing",
        name="Wiatr kierunek",
        native_unit_of_measurement="°",
        icon="mdi:compass",
        value_fn=lambda d: d["current"].get("wind_direction_10m"),
    ),
    OpenMeteoSensorDescription(
        key="cloud_cover",
        name="Zachmurzenie",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cloud",
        value_fn=lambda d: d["current"].get("cloud_cover"),
    ),
    OpenMeteoSensorDescription(
        key="precipitation",
        name="Opady aktualne",
        native_unit_of_measurement="mm",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-rainy",
        value_fn=lambda d: d["current"].get("precipitation"),
    ),
    OpenMeteoSensorDescription(
        key="uv_index",
        name="UV Index max",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny-alert",
        value_fn=lambda d: d["daily"][0].get("uv_index_max") if d.get("daily") else None,
    ),
    OpenMeteoSensorDescription(
        key="sunrise",
        name="Wschód słońca",
        icon="mdi:weather-sunset-up",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _parse_iso(d["daily"][0].get("sunrise")) if d.get("daily") else None,
    ),
    OpenMeteoSensorDescription(
        key="sunset",
        name="Zachód słońca",
        icon="mdi:weather-sunset-down",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _parse_iso(d["daily"][0].get("sunset")) if d.get("daily") else None,
    ),
    OpenMeteoSensorDescription(
        key="condition_label",
        name="Opis pogody",
        icon="mdi:weather-partly-cloudy",
        value_fn=lambda d: WMO_LABELS.get(d["current"].get("weather_code", 0), ""),
    ),
)


def _parse_iso(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: OpenMeteoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [OpenMeteoSensor(coordinator, entry, desc) for desc in SENSORS],
        True,
    )


class OpenMeteoSensor(CoordinatorEntity, SensorEntity):
    entity_description: OpenMeteoSensorDescription

    def __init__(
        self,
        coordinator: OpenMeteoCoordinator,
        entry: ConfigEntry,
        description: OpenMeteoSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        location = entry.data[CONF_NAME]
        self._attr_name = f"{location} {description.name}"
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self):
        try:
            return self.entity_description.value_fn(self.coordinator.data)
        except (KeyError, IndexError, TypeError):
            return None

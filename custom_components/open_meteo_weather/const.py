DOMAIN = "open_meteo_weather"
PLATFORMS = ["weather", "sensor"]

CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_NAME = "name"
CONF_TIMEZONE = "timezone"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_UPDATE_INTERVAL = 600  # 10 minut
DEFAULT_TIMEZONE = "Europe/Warsaw"

API_URL = "https://api.open-meteo.com/v1/forecast"

CARD_URL = "/open_meteo_weather/card.js"
CARD_VERSION = "1.0.0"

WMO_LABELS = {
    0: "Słonecznie",
    1: "Głównie słonecznie",
    2: "Częściowe zachmurzenie",
    3: "Pochmurno",
    45: "Mgła",
    48: "Mgła osadzająca szron",
    51: "Mżawka słaba",
    53: "Mżawka",
    55: "Mżawka silna",
    56: "Marznąca mżawka",
    57: "Marznąca mżawka silna",
    61: "Deszcz słaby",
    63: "Deszcz",
    65: "Deszcz silny",
    66: "Marznący deszcz",
    67: "Marznący deszcz silny",
    71: "Śnieg słaby",
    73: "Śnieg",
    75: "Śnieg silny",
    77: "Ziarna śnieżne",
    80: "Przelotne opady słabe",
    81: "Przelotne opady",
    82: "Gwałtowne opady",
    85: "Przelotny śnieg słaby",
    86: "Przelotny śnieg silny",
    95: "Burza",
    96: "Burza z gradem",
    99: "Burza z gradem silna",
}


def wmo_to_condition(code: int, is_day: int = 1) -> str:
    if code == 0:
        return "sunny" if is_day else "clear-night"
    if code in (1, 2):
        return "partlycloudy"
    if code == 3:
        return "cloudy"
    if code in (45, 48):
        return "fog"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "rainy"
    if code in (71, 73, 75, 77, 85, 86):
        return "snowy"
    if code in (95, 96, 99):
        return "lightning-rainy"
    return "exceptional"

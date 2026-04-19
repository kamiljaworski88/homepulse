"""Constants for rehab_monitor integration.

API confirmed via DevTools on 2026-04-16 against erj.intermedicus.pl/Portal.
"""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "rehab_monitor"
SCAN_INTERVAL = timedelta(minutes=15)
HOUR_START = 7
HOUR_END = 23

PLATFORMS = ["switch", "select", "sensor", "binary_sensor", "button", "number"]

# ── Config entry keys ─────────────────────────────────────────────────────────
CONF_LOGIN = "login"
CONF_HASLO = "haslo"
CONF_NOTIFY_SERVICE = "notify_service"
CONF_PLACE_ID_TERAPIA = "place_id_terapia"
CONF_PLACE_ID_SI = "place_id_si"

# ── Place IDs ─────────────────────────────────────────────────────────────────
# Confirmed via DevTools: PlaceId=7 for "Terapia dzieci".
# TODO: Open portal, select "SI-1-1", capture FreeTermsFilter payload,
#       note the PlaceId value and update DEFAULT_PLACE_ID_SI below.
DEFAULT_PLACE_ID_TERAPIA = "7"
DEFAULT_PLACE_ID_SI = "10"  # Confirmed via DevTools: PlaceId=10 for SI-1-1

# ── Place names (must match select entity options exactly) ───────────────────
MIEJSCE_TERAPIA = "Terapia dzieci"
MIEJSCE_SI = "SI-1-1"
MIEJSCE_OBE = "Obie"
MIEJSCA: list[str] = [MIEJSCE_TERAPIA, MIEJSCE_SI, MIEJSCE_OBE]

# ── Date format confirmed via DevTools (FreeTermsFilter DateFrom/DateTo) ─────
DATE_FORMAT = "%d.%m.%Y"   # e.g. "16.04.2026"

# ── API URLs ──────────────────────────────────────────────────────────────────
URL_BASE = "https://erj.intermedicus.pl/Portal"
URL_LOGIN_PAGE = f"{URL_BASE}/Account/Login"
URL_TERMS_INDEX = f"{URL_BASE}/Terms"   # GET this to obtain a fresh CSRF token
URL_FREE_TERMS_FILTER = f"{URL_BASE}/Terms/FreeTermsFilter"
URL_GET_FREE_TERMS = f"{URL_BASE}/Terms/GetFreeTerms"

# ── GetFreeTerms response: wrapper key ───────────────────────────────────────
# Confirmed: response is {"Data": [...], "Total": n, ...}
RESP_DATA_WRAPPER_KEY = "Data"

# ── GetFreeTerms response: per-slot field names (confirmed via DevTools) ──────
# To update after a portal upgrade: capture GetFreeTerms response in DevTools
# and update the constants below.  Wzorzec analogiczny do ecoharmonogram_pl
# gdzie endpoint zmienił się po aktualizacji.
RESP_FIELD_ID = "Id"                # int — unique slot identifier, e.g. 6312851
RESP_FIELD_DATE = "StartDate"       # str — ISO datetime "2026-04-17T14:40:00"
RESP_FIELD_TIME = "StartTime"       # str — "14:40"
RESP_FIELD_DOCTOR = "PersonelName"  # str — "Jurek-Pruska Justyna"
RESP_FIELD_PLACE = "PlaceName"      # str — "Terapia Dzieci"
RESP_FIELD_IS_BOOKED = "IsBooked"   # bool — FALSE means the slot is FREE
# Note: all records in GetFreeTerms are free terms; IsBooked is a safety filter.

# ── FreeTermsFilter form field names (confirmed via DevTools) ────────────────
# Request is application/x-www-form-urlencoded (NOT JSON).
REQ_FIELD_FREE_TERMS_SUBMIT = "FreeTermsSubmit"   # submit button name; value=""
REQ_FIELD_WITHOUT_PERSONEL = "WithoutPersonel"     # value: "False"
REQ_FIELD_PROVIDER_ID = "ProviderId"               # value: "1"
REQ_FIELD_SPECIALITY_ID = "SpecialityId"           # value: "" (leave empty)
REQ_FIELD_SERVICE_ID = "ServiceId"                 # value: "" (leave empty)
REQ_FIELD_PERSONEL_ID = "PersonelId"               # value: "" (leave empty)
REQ_FIELD_PLACE_ID = "PlaceId"                     # value: e.g. "7"
REQ_FIELD_FILTER_TYPE_ID = "FilterTypeId"          # value: "3"
REQ_FIELD_DATE_FROM = "DateFrom"                   # value: "16.04.2026"
REQ_FIELD_DATE_TO = "DateTo"                       # value: "15.05.2026"

# Fixed values for FreeTermsFilter fields
REQ_VALUE_WITHOUT_PERSONEL = "False"
REQ_VALUE_PROVIDER_ID = "1"
REQ_VALUE_FILTER_TYPE_ID = "3"

# ── Login form field names (ASP.NET MVC defaults) ────────────────────────────
# TODO: Verify via DevTools if login is required for this portal installation.
LOGIN_FIELD_USERNAME = "UserName"
LOGIN_FIELD_PASSWORD = "Password"
CSRF_FORM_FIELD = "__RequestVerificationToken"

# ── GetFreeTerms form fields (Kendo UI Grid pagination — confirmed via DevTools) ─
# GetFreeTerms also uses application/x-www-form-urlencoded.
# Payload: sort=&page=1&pageSize=20&group=&filter=&__RequestVerificationToken=...
REQ_FIELD_GET_SORT = "sort"
REQ_FIELD_GET_PAGE = "page"
REQ_FIELD_GET_PAGE_SIZE = "pageSize"
REQ_FIELD_GET_GROUP = "group"
REQ_FIELD_GET_FILTER = "filter"
REQ_VALUE_GET_PAGE = "1"
REQ_VALUE_GET_PAGE_SIZE = "20"

# ── Coordinator data dict keys ────────────────────────────────────────────────
DATA_TERMINY = "terminy"
DATA_COUNT = "count"
DATA_LAST_UPDATE = "ostatnia_aktualizacja"
DATA_ERROR = "blad"

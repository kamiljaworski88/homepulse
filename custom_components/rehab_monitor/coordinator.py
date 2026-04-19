"""Data update coordinator for rehab_monitor.

API confirmed via DevTools on 2026-04-16:

FreeTermsFilter — POST application/x-www-form-urlencoded
  Fields: FreeTermsSubmit, WithoutPersonel, ProviderId, SpecialityId,
          ServiceId, PersonelId, PlaceId, FilterTypeId, DateFrom, DateTo,
          __RequestVerificationToken
  Header: X-Requested-With: XMLHttpRequest

GetFreeTerms — POST (CSRF token in body)
  Response: {"Data": [...slots...], "Total": n, ...}
  Per slot: Id, StartDate (ISO datetime), StartTime, PersonelName, PlaceName,
            IsBooked (False = free)

Session / CSRF lifecycle:
  1. GET Terms/Index  →  extract __RequestVerificationToken from HTML
  2. Store token for the session lifetime
  3. Send token as form field in every FreeTermsFilter POST
  4. On 400/401/403 or login redirect → refresh CSRF token (and re-login if needed)
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_HASLO,
    CONF_LOGIN,
    CONF_NOTIFY_SERVICE,
    CONF_PLACE_ID_SI,
    CONF_PLACE_ID_TERAPIA,
    CSRF_FORM_FIELD,
    DATA_COUNT,
    DATA_ERROR,
    DATA_LAST_UPDATE,
    DATA_TERMINY,
    DATE_FORMAT,
    DEFAULT_PLACE_ID_SI,
    DEFAULT_PLACE_ID_TERAPIA,
    DOMAIN,
    HOUR_END,
    HOUR_START,
    LOGIN_FIELD_PASSWORD,
    LOGIN_FIELD_USERNAME,
    MIEJSCE_OBE,
    MIEJSCE_SI,
    MIEJSCE_TERAPIA,
    REQ_FIELD_DATE_FROM,
    REQ_FIELD_DATE_TO,
    REQ_FIELD_FILTER_TYPE_ID,
    REQ_FIELD_FREE_TERMS_SUBMIT,
    REQ_FIELD_GET_FILTER,
    REQ_FIELD_GET_GROUP,
    REQ_FIELD_GET_PAGE,
    REQ_FIELD_GET_PAGE_SIZE,
    REQ_FIELD_GET_SORT,
    REQ_FIELD_PERSONEL_ID,
    REQ_FIELD_PLACE_ID,
    REQ_FIELD_PROVIDER_ID,
    REQ_FIELD_SERVICE_ID,
    REQ_FIELD_SPECIALITY_ID,
    REQ_FIELD_WITHOUT_PERSONEL,
    REQ_VALUE_FILTER_TYPE_ID,
    REQ_VALUE_GET_PAGE,
    REQ_VALUE_GET_PAGE_SIZE,
    REQ_VALUE_PROVIDER_ID,
    REQ_VALUE_WITHOUT_PERSONEL,
    RESP_DATA_WRAPPER_KEY,
    RESP_FIELD_DATE,
    RESP_FIELD_DOCTOR,
    RESP_FIELD_ID,
    RESP_FIELD_IS_BOOKED,
    RESP_FIELD_PLACE,
    RESP_FIELD_TIME,
    SCAN_INTERVAL,
    URL_BASE,
    URL_FREE_TERMS_FILTER,
    URL_GET_FREE_TERMS,
    URL_LOGIN_PAGE,
    URL_TERMS_INDEX,
)

_LOGGER = logging.getLogger(__name__)

_AJAX_HEADER = "XMLHttpRequest"


def _empty_data() -> dict[str, Any]:
    return {
        DATA_TERMINY: [],
        DATA_COUNT: 0,
        DATA_LAST_UPDATE: None,
        DATA_ERROR: None,
    }


def _extract_csrf_token(html: str) -> str | None:
    """Extract ASP.NET __RequestVerificationToken from an HTML page.

    Tries the three attribute orderings that Razor / MVC can emit.
    """
    for pattern in (
        r'name="__RequestVerificationToken"[^>]+value="([^"]+)"',
        r'value="([^"]+)"[^>]+name="__RequestVerificationToken"',
        r'<meta[^>]+name="csrf-token"[^>]+content="([^"]+)"',
    ):
        m = re.search(pattern, html)
        if m:
            return m.group(1)
    return None


def _is_login_redirect(url: str) -> bool:
    return "/Account/Login" in url or "/Account/SignIn" in url


def _parse_start_date(raw: str) -> str:
    """Convert ISO datetime string '2026-04-17T14:40:00' → '2026-04-17'."""
    return raw.split("T")[0] if "T" in raw else raw


class RehabDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the Intermedicus portal for free rehabilitation slots."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self._config = config_entry.data
        self._session: aiohttp.ClientSession | None = None
        self._logged_in: bool = False
        self._csrf_token: str = ""

        # Deduplication set: slot IDs for which a notification was already sent.
        # Slots removed from the API response are evicted so they can re-notify
        # if they reappear (cancelled → re-opened appointment).
        self.sent_slot_ids: set[str] = set()

        # Set by switch / select entities; coordinator reads these on each tick.
        self.monitor_active: bool = True
        self.miejsce: str = MIEJSCE_TERAPIA

        # When True the next _async_update_data call bypasses the hours check.
        # Set by force_refresh() so the manual button always works.
        self._force_refresh: bool = False

        # Dynamic schedule — overridden by number entities after restore.
        self._hour_start: int = HOUR_START
        self._hour_end: int = HOUR_END

        # Minimum visit hour — slots earlier than this hour are ignored.
        # 0 = show all (no filter).
        self._visit_hour_min: int = 0

    # ── lifecycle ─────────────────────────────────────────────────────────────

    async def async_setup(self) -> None:
        """Create the shared aiohttp session.  Call once from async_setup_entry.

        SSL verification is disabled because erj.intermedicus.pl uses a certificate
        with an unverifiable intermediate CA on the default system trust store.
        All traffic is still encrypted (HTTPS); only chain verification is skipped.
        """
        connector = aiohttp.TCPConnector(ssl=False)
        self._session = aiohttp.ClientSession(
            connector=connector,
            cookie_jar=aiohttp.CookieJar(),
            timeout=aiohttp.ClientTimeout(connect=10, sock_read=15),
        )

    async def async_shutdown(self) -> None:
        """Close the shared session.  Call from async_unload_entry."""
        if self._session is not None:
            await self._session.close()
            self._session = None
        self._logged_in = False
        self._csrf_token = ""

    # ── public helpers ────────────────────────────────────────────────────────

    def set_monitor_active(self, active: bool) -> None:
        self.monitor_active = active

    def set_miejsce(self, miejsce: str) -> None:
        self.miejsce = miejsce

    async def force_refresh(self) -> None:
        """Trigger an immediate poll bypassing the active-hours window."""
        self._force_refresh = True
        await self.async_request_refresh()

    def set_scan_interval(self, minutes: int) -> None:
        """Update polling interval and reschedule immediately."""
        self.update_interval = timedelta(minutes=max(1, minutes))
        # Cancel the already-queued callback and reschedule with the new interval
        # so the change takes effect without waiting for the current cycle to finish.
        if self._unsub_refresh:
            self._unsub_refresh()
            self._unsub_refresh = None
        self._schedule_refresh()

    def set_hour_start(self, hour: int) -> None:
        self._hour_start = max(0, min(hour, 22))

    def set_hour_end(self, hour: int) -> None:
        self._hour_end = max(1, min(hour, 24))

    def set_visit_hour_min(self, hour: int) -> None:
        """Ignore slots whose start time is before this hour. 0 = no filter."""
        self._visit_hour_min = max(0, min(hour, 23))

    # ── coordinator core ──────────────────────────────────────────────────────

    async def _async_update_data(self) -> dict[str, Any]:
        last = self.data or _empty_data()

        forced = self._force_refresh
        self._force_refresh = False  # consume the flag regardless of outcome

        if not self.monitor_active:
            return last
        if not forced and not self._is_active_hours():
            return last

        try:
            await self._ensure_session()

            terminy: list[dict[str, Any]] = []
            if self.miejsce == MIEJSCE_OBE:
                for m in (MIEJSCE_TERAPIA, MIEJSCE_SI):
                    terminy.extend(await self._fetch_terms(m))
            else:
                terminy = await self._fetch_terms(self.miejsce)

            current_ids = {t["slot_id"] for t in terminy}
            new_slots = [t for t in terminy if t["slot_id"] not in self.sent_slot_ids]
            self.sent_slot_ids -= self.sent_slot_ids - current_ids  # evict gone slots

            await self._send_notifications(new_slots)
            for slot in new_slots:
                self.sent_slot_ids.add(slot["slot_id"])

            return {
                DATA_TERMINY: terminy,
                DATA_COUNT: len(terminy),
                DATA_LAST_UPDATE: datetime.now().isoformat(timespec="seconds"),
                DATA_ERROR: None,
            }

        except aiohttp.ClientConnectorError as err:
            _LOGGER.warning("rehab_monitor: network error — %s", err)
            return {**last, DATA_ERROR: f"Błąd sieci: {err}"}

        except asyncio.TimeoutError:
            _LOGGER.warning("rehab_monitor: request timed out")
            return {**last, DATA_ERROR: "Przekroczono czas oczekiwania"}

        except aiohttp.ClientResponseError as err:
            _LOGGER.error("rehab_monitor: HTTP %s — %s", err.status, err.message)
            return {**last, DATA_ERROR: f"HTTP {err.status}"}

        except ValueError as err:
            # json.JSONDecodeError is a subclass of ValueError
            _LOGGER.warning(
                "rehab_monitor: JSON decode error — portal probably returned HTML "
                "(session expired?). Detail: %s",
                err,
            )
            self._logged_in = False
            self._csrf_token = ""
            return {**last, DATA_ERROR: "Nieprawidłowa odpowiedź serwera (HTML zamiast JSON)"}

        except (KeyError, IndexError) as err:
            # TODO: Jeśli API portalu zmieni strukturę odpowiedzi, zaktualizuj
            # parsowanie w metodzie _parse_terms(). Wzorzec analogiczny do
            # ecoharmonogram_pl gdzie endpoint zmienił się po aktualizacji.
            _LOGGER.error(
                "rehab_monitor: unexpected API structure — update _parse_terms(). "
                "Missing key/index: %s",
                err,
            )
            return {**last, DATA_ERROR: f"Nieoczekiwana struktura API: {err}"}

    # ── time guard ────────────────────────────────────────────────────────────

    def _is_active_hours(self) -> bool:
        tz = ZoneInfo(self.hass.config.time_zone)
        now = datetime.now(tz)
        return self._hour_start <= now.hour < self._hour_end

    # ── auth & CSRF ───────────────────────────────────────────────────────────

    async def _ensure_session(self) -> None:
        """Obtain a CSRF token (and log in if credentials are configured)."""
        login = self._config.get(CONF_LOGIN, "").strip()
        if login and not self._logged_in:
            await self._login()
        if not self._csrf_token:
            await self._refresh_csrf_token()

    async def _refresh_csrf_token(self) -> None:
        """GET the Terms page and extract the anti-forgery token.

        Tries URL_TERMS_INDEX first, then URL_BASE as fallback.
        """
        assert self._session is not None

        for url in (URL_TERMS_INDEX, URL_BASE):
            _LOGGER.debug("rehab_monitor: fetching CSRF token from %s", url)
            async with self._session.get(url) as resp:
                final_url = str(resp.url)
                if _is_login_redirect(final_url):
                    _LOGGER.debug("rehab_monitor: redirected to login page, attempting login")
                    self._logged_in = False
                    await self._login()
                    async with self._session.get(url) as resp2:
                        html = await resp2.text()
                else:
                    html = await resp.text()

            token = _extract_csrf_token(html)
            if token:
                self._csrf_token = token
                _LOGGER.debug(
                    "rehab_monitor: CSRF token obtained from %s (%d chars)",
                    url, len(token),
                )
                return

        _LOGGER.warning(
            "rehab_monitor: __RequestVerificationToken not found on any page. "
            "FreeTermsFilter will likely fail with HTTP 400."
        )

    async def _login(self) -> None:
        """Full login: GET login page → extract CSRF → POST credentials."""
        assert self._session is not None
        login = self._config.get(CONF_LOGIN, "")
        password = self._config.get(CONF_HASLO, "")

        _LOGGER.debug("rehab_monitor: fetching login page")
        async with self._session.get(URL_LOGIN_PAGE) as resp:
            resp.raise_for_status()
            html = await resp.text()

        csrf = _extract_csrf_token(html)
        if not csrf:
            _LOGGER.error(
                "rehab_monitor: no CSRF token on login page — "
                "cannot authenticate. Check LOGIN_FIELD_* in const.py."
            )
            return

        form = aiohttp.FormData()
        form.add_field(CSRF_FORM_FIELD, csrf)
        form.add_field(LOGIN_FIELD_USERNAME, login)
        form.add_field(LOGIN_FIELD_PASSWORD, password)

        _LOGGER.debug("rehab_monitor: posting login credentials")
        async with self._session.post(
            URL_LOGIN_PAGE,
            data=form,
            headers={"X-Requested-With": _AJAX_HEADER},
        ) as resp:
            body = await resp.text()
            final_url = str(resp.url)

        if _is_login_redirect(final_url):
            _LOGGER.error(
                "rehab_monitor: login failed (still on login page). "
                "Check login/password in integration config."
            )
            return

        self._logged_in = True
        # Grab CSRF token from the post-login page for subsequent form posts
        token = _extract_csrf_token(body)
        if token:
            self._csrf_token = token

        _LOGGER.info("rehab_monitor: login successful")

    # ── fetch ─────────────────────────────────────────────────────────────────

    def _get_place_id(self, miejsce: str) -> str:
        return {
            MIEJSCE_TERAPIA: self._config.get(CONF_PLACE_ID_TERAPIA, DEFAULT_PLACE_ID_TERAPIA),
            MIEJSCE_SI: self._config.get(CONF_PLACE_ID_SI, DEFAULT_PLACE_ID_SI),
        }.get(miejsce, DEFAULT_PLACE_ID_TERAPIA)

    def _build_filter_form(self, miejsce: str) -> aiohttp.FormData:
        """Build the application/x-www-form-urlencoded body for FreeTermsFilter."""
        from_date = date.today()
        to_date = from_date + timedelta(days=30)

        form = aiohttp.FormData()
        form.add_field(REQ_FIELD_FREE_TERMS_SUBMIT, "")
        form.add_field(REQ_FIELD_WITHOUT_PERSONEL, REQ_VALUE_WITHOUT_PERSONEL)
        form.add_field(REQ_FIELD_PROVIDER_ID, REQ_VALUE_PROVIDER_ID)
        form.add_field(REQ_FIELD_SPECIALITY_ID, "")
        form.add_field(REQ_FIELD_SERVICE_ID, "")
        form.add_field(REQ_FIELD_PERSONEL_ID, "")
        form.add_field(REQ_FIELD_PLACE_ID, self._get_place_id(miejsce))
        form.add_field(REQ_FIELD_FILTER_TYPE_ID, REQ_VALUE_FILTER_TYPE_ID)
        form.add_field(REQ_FIELD_DATE_FROM, from_date.strftime(DATE_FORMAT))
        form.add_field(REQ_FIELD_DATE_TO, to_date.strftime(DATE_FORMAT))
        form.add_field(CSRF_FORM_FIELD, self._csrf_token)
        return form

    async def _fetch_terms(self, miejsce: str) -> list[dict[str, Any]]:
        """Run FreeTermsFilter → GetFreeTerms for one place, with auto-retry on 400/401/403."""
        assert self._session is not None

        headers = {"X-Requested-With": _AJAX_HEADER}

        # ── Step 1: POST FreeTermsFilter (sets server-side session filter) ────
        filter_form = self._build_filter_form(miejsce)
        _LOGGER.debug(
            "rehab_monitor: POST FreeTermsFilter — miejsce=%s placeId=%s csrf=%s…",
            miejsce, self._get_place_id(miejsce),
            self._csrf_token[:12] if self._csrf_token else "(brak!)",
        )
        async with self._session.post(
            URL_FREE_TERMS_FILTER, data=filter_form, headers=headers
        ) as resp:
            _LOGGER.debug("rehab_monitor: FreeTermsFilter → HTTP %s", resp.status)
            if resp.status in (400, 401, 403) or _is_login_redirect(str(resp.url)):
                _LOGGER.info(
                    "rehab_monitor: FreeTermsFilter HTTP %s — odświeżam CSRF i powtarzam",
                    resp.status,
                )
                self._csrf_token = ""
                self._logged_in = False
                await self._ensure_session()
                filter_form = self._build_filter_form(miejsce)
                async with self._session.post(
                    URL_FREE_TERMS_FILTER, data=filter_form, headers=headers
                ) as retry_resp:
                    _LOGGER.debug(
                        "rehab_monitor: FreeTermsFilter retry → HTTP %s", retry_resp.status
                    )
                    retry_resp.raise_for_status()
            else:
                resp.raise_for_status()

        # ── Step 2: POST GetFreeTerms (Kendo UI Grid pagination params + CSRF) ──
        # Confirmed payload: sort=&page=1&pageSize=20&group=&filter=&__RequestVerificationToken=...
        get_form = aiohttp.FormData()
        get_form.add_field(REQ_FIELD_GET_SORT, "")
        get_form.add_field(REQ_FIELD_GET_PAGE, REQ_VALUE_GET_PAGE)
        get_form.add_field(REQ_FIELD_GET_PAGE_SIZE, REQ_VALUE_GET_PAGE_SIZE)
        get_form.add_field(REQ_FIELD_GET_GROUP, "")
        get_form.add_field(REQ_FIELD_GET_FILTER, "")
        get_form.add_field(CSRF_FORM_FIELD, self._csrf_token)

        _LOGGER.debug("rehab_monitor: POST GetFreeTerms")
        async with self._session.post(
            URL_GET_FREE_TERMS, data=get_form, headers=headers
        ) as resp:
            _LOGGER.debug("rehab_monitor: GetFreeTerms → HTTP %s", resp.status)
            resp.raise_for_status()
            raw = await resp.json(content_type=None)

        total = raw.get("Total", "?") if isinstance(raw, dict) else "?"
        _LOGGER.debug(
            "rehab_monitor: GetFreeTerms zwrócił Total=%s dla miejsca '%s'",
            total, miejsce,
        )
        return self._parse_terms(raw, miejsce)

    # ── parse ─────────────────────────────────────────────────────────────────

    def _parse_terms(self, raw: Any, miejsce: str) -> list[dict[str, Any]]:
        """Normalise GetFreeTerms JSON response to a list of internal slot dicts.

        Confirmed response shape (2026-04-16):
          {"Data": [...], "Total": n, "AggregateResults": null, "Errors": null}

        Each slot:
          Id            int       6312851
          StartDate     str       "2026-04-17T14:40:00"
          StartTime     str       "14:40"
          PersonelName  str       "Jurek-Pruska Justyna"
          PlaceName     str       "Terapia Dzieci"
          IsBooked      bool      false  ← False = free slot

        TODO: Jeśli API portalu zmieni strukturę odpowiedzi, zaktualizuj
        parsowanie poniżej. Wzorzec analogiczny do ecoharmonogram_pl gdzie
        endpoint zmienił się po aktualizacji.
        """
        # Unwrap {"Data": [...]} envelope
        items: Any = raw.get(RESP_DATA_WRAPPER_KEY, []) if isinstance(raw, dict) else raw

        if not isinstance(items, list):
            _LOGGER.warning(
                "rehab_monitor: expected list under '%s', got %s — "
                "check RESP_DATA_WRAPPER_KEY in const.py",
                RESP_DATA_WRAPPER_KEY,
                type(items).__name__,
            )
            return []

        results: list[dict[str, Any]] = []
        for item in items:
            try:
                # IsBooked: false → slot is free; true → already taken
                if item.get(RESP_FIELD_IS_BOOKED, False):
                    continue

                slot_id = str(item[RESP_FIELD_ID])
                raw_date = str(item.get(RESP_FIELD_DATE, ""))
                godzina = str(item.get(RESP_FIELD_TIME, ""))

                # Apply minimum-hour filter (0 = disabled)
                if self._visit_hour_min > 0:
                    try:
                        slot_hour = int(godzina.split(":")[0])
                        if slot_hour < self._visit_hour_min:
                            continue
                    except (ValueError, IndexError):
                        pass  # malformed time — include the slot rather than drop it

                results.append(
                    {
                        "slot_id": slot_id,
                        "data": _parse_start_date(raw_date),
                        "godzina": godzina,
                        "rehabilitant": str(item.get(RESP_FIELD_DOCTOR, "")),
                        "miejsce": str(item.get(RESP_FIELD_PLACE, miejsce)),
                    }
                )
            except (KeyError, TypeError) as err:
                _LOGGER.warning(
                    "rehab_monitor: skipping malformed slot entry (%s). Item: %s",
                    err,
                    item,
                )

        return results

    # ── notifications ─────────────────────────────────────────────────────────

    async def _send_notifications(self, new_slots: list[dict[str, Any]]) -> None:
        notify_service = self._config.get(CONF_NOTIFY_SERVICE, "").strip()
        if not notify_service or not new_slots:
            return

        for slot in new_slots:
            message = (
                f"📅 {slot['data']} {slot['godzina']}\n"
                f"👤 {slot['rehabilitant']}\n"
                f"🏥 {slot['miejsce']}"
            )
            try:
                await self.hass.services.async_call(
                    "notify",
                    notify_service,
                    {"title": "Wolny termin rehabilitacji!", "message": message},
                )
                _LOGGER.info(
                    "rehab_monitor: notification sent — slot %s (%s %s)",
                    slot["slot_id"], slot["data"], slot["godzina"],
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.error(
                    "rehab_monitor: failed to send notification via '%s': %s",
                    notify_service,
                    err,
                )

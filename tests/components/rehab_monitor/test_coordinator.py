"""Unit tests for RehabDataUpdateCoordinator.

Run with:  pytest tests/components/rehab_monitor/ -v

Dependencies (add to requirements_test.txt / pyproject.toml):
  pytest
  pytest-asyncio
  aioresponses
  homeassistant (or pytest-homeassistant-custom-component)
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioresponses import aioresponses

from custom_components.rehab_monitor.const import (
    CONF_NOTIFY_SERVICE,
    CONF_PLACE_ID_TERAPIA,
    DATA_COUNT,
    DATA_ERROR,
    DATA_TERMINY,
    DATE_FORMAT,
    DEFAULT_PLACE_ID_TERAPIA,
    DOMAIN,
    MIEJSCE_TERAPIA,
    RESP_DATA_WRAPPER_KEY,
    URL_FREE_TERMS_FILTER,
    URL_GET_FREE_TERMS,
)
from custom_components.rehab_monitor.coordinator import RehabDataUpdateCoordinator

# ── helpers ───────────────────────────────────────────────────────────────────

MOCK_SLOT: dict[str, Any] = {
    "id": "slot-001",
    "date": "2025-05-10",
    "hour": "10:30",
    "doctorName": "Kowalski J.",
    "placeName": "Terapia dzieci",
    "isFree": True,
}

MOCK_SLOT_2: dict[str, Any] = {
    "id": "slot-002",
    "date": "2025-05-11",
    "hour": "11:00",
    "doctorName": "Nowak A.",
    "placeName": "Terapia dzieci",
    "isFree": True,
}


def _make_config_entry(
    notify: str = "mobile_app_test",
    place_id: str = DEFAULT_PLACE_ID_TERAPIA,
    login: str = "",
    haslo: str = "",
) -> MagicMock:
    entry = MagicMock()
    entry.data = {
        CONF_NOTIFY_SERVICE: notify,
        CONF_PLACE_ID_TERAPIA: place_id,
        "login": login,
        "haslo": haslo,
    }
    return entry


def _make_hass(hour: int = 10, time_zone: str = "Europe/Warsaw") -> MagicMock:
    hass = MagicMock()
    hass.config.time_zone = time_zone
    hass.services.async_call = AsyncMock()
    return hass


def _response_body(slots: list[dict]) -> Any:
    """Return the mock API response in whatever shape RESP_DATA_WRAPPER_KEY dictates."""
    if RESP_DATA_WRAPPER_KEY:
        return {RESP_DATA_WRAPPER_KEY: slots}
    return slots


def _expected_date_params() -> dict[str, str]:
    from_date = date.today()
    to_date = from_date + timedelta(days=30)
    return {
        "dateFrom": from_date.strftime(DATE_FORMAT),
        "dateTo": to_date.strftime(DATE_FORMAT),
    }


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def coordinator() -> RehabDataUpdateCoordinator:
    hass = _make_hass()
    entry = _make_config_entry()
    coord = RehabDataUpdateCoordinator(hass, entry)
    coord.monitor_active = True
    coord.miejsce = MIEJSCE_TERAPIA
    return coord


# ── test_fetch_terms_success ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_terms_success(coordinator: RehabDataUpdateCoordinator) -> None:
    """Happy path: FreeTermsFilter + GetFreeTerms return one free slot.

    Asserts:
    - coordinator.data["count"] == 1
    - coordinator.data["terminy"] contains the expected slot fields
    - No error attribute
    """
    import aiohttp

    with aioresponses() as m:
        # FreeTermsFilter returns 200 (body doesn't matter — we only check status)
        m.post(URL_FREE_TERMS_FILTER, status=200, payload={"ok": True})
        # GetFreeTerms returns one free slot
        m.post(URL_GET_FREE_TERMS, status=200, payload=_response_body([MOCK_SLOT]))

        coordinator._session = aiohttp.ClientSession()
        try:
            data = await coordinator._async_update_data()
        finally:
            await coordinator._session.close()

    assert data[DATA_COUNT] == 1
    assert len(data[DATA_TERMINY]) == 1
    slot = data[DATA_TERMINY][0]
    assert slot["slot_id"] == "slot-001"
    assert slot["data"] == "2025-05-10"
    assert slot["godzina"] == "10:30"
    assert slot["rehabilitant"] == "Kowalski J."
    assert data[DATA_ERROR] is None


# ── test_fetch_terms_outside_hours ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_terms_outside_hours(
    coordinator: RehabDataUpdateCoordinator,
) -> None:
    """Outside the 07:00–23:00 window no HTTP requests must be made.

    We patch _is_active_hours to return False and verify that the coordinator
    returns the last known data without touching the network.
    """
    coordinator.data = {  # type: ignore[assignment]
        DATA_TERMINY: [],
        DATA_COUNT: 0,
        "ostatnia_aktualizacja": "2025-05-01T06:00:00",
        DATA_ERROR: None,
    }

    with patch.object(coordinator, "_is_active_hours", return_value=False):
        with aioresponses() as m:
            data = await coordinator._async_update_data()
            # aioresponses would raise ConnectionError if any request was made
            assert m.requests == {}  # no requests registered means none were sent

    assert data[DATA_COUNT] == 0
    assert data[DATA_ERROR] is None


# ── test_fetch_terms_session_expired ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_terms_session_expired(
    coordinator: RehabDataUpdateCoordinator,
) -> None:
    """HTTP 401 on FreeTermsFilter triggers re-login then successful retry.

    Scenario:
    1. First POST /FreeTermsFilter → 401
    2. Coordinator calls _login() (mocked to succeed instantly)
    3. Retry POST /FreeTermsFilter → 200
    4. POST /GetFreeTerms → 200 with one slot
    """
    import aiohttp

    coordinator._config = {
        **coordinator._config,
        "login": "testuser",
        "haslo": "testpass",
    }

    login_called: list[bool] = []

    async def mock_login(self_: Any = None) -> None:  # noqa: ANN001
        login_called.append(True)
        coordinator._logged_in = True

    with aioresponses() as m:
        # First attempt → 401 (session expired)
        m.post(URL_FREE_TERMS_FILTER, status=401)
        # After re-login retry → 200
        m.post(URL_FREE_TERMS_FILTER, status=200, payload={"ok": True})
        m.post(URL_GET_FREE_TERMS, status=200, payload=_response_body([MOCK_SLOT]))

        coordinator._session = aiohttp.ClientSession()
        try:
            with patch.object(
                RehabDataUpdateCoordinator, "_login", new=AsyncMock(side_effect=mock_login)
            ):
                data = await coordinator._async_update_data()
        finally:
            await coordinator._session.close()

    assert len(login_called) == 1, "Expected exactly one re-login call"
    assert data[DATA_COUNT] == 1
    assert data[DATA_ERROR] is None


# ── test_notification_deduplication ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_notification_deduplication(
    coordinator: RehabDataUpdateCoordinator,
) -> None:
    """The same slot must not trigger more than one push notification.

    First poll: slot-001 is new → notify called once.
    Second poll: slot-001 is still present → notify NOT called again.
    Third poll: slot-001 disappears → removed from sent_slot_ids.
    Fourth poll: slot-001 reappears → notify called again (fresh slot).
    """
    import aiohttp

    def _mock_responses(m: aioresponses, slots: list[dict]) -> None:
        m.post(URL_FREE_TERMS_FILTER, status=200, payload={"ok": True})
        m.post(URL_GET_FREE_TERMS, status=200, payload=_response_body(slots))

    hass = coordinator.hass
    coordinator._session = aiohttp.ClientSession()

    try:
        # ── Poll 1: new slot ──────────────────────────────────────────────
        with aioresponses() as m:
            _mock_responses(m, [MOCK_SLOT])
            await coordinator._async_update_data()

        assert hass.services.async_call.await_count == 1
        assert "slot-001" in coordinator.sent_slot_ids

        # ── Poll 2: same slot, no new notification ────────────────────────
        with aioresponses() as m:
            _mock_responses(m, [MOCK_SLOT])
            await coordinator._async_update_data()

        assert hass.services.async_call.await_count == 1  # still 1, not 2

        # ── Poll 3: slot disappears ────────────────────────────────────────
        with aioresponses() as m:
            _mock_responses(m, [])
            await coordinator._async_update_data()

        assert "slot-001" not in coordinator.sent_slot_ids

        # ── Poll 4: slot reappears → new notification ─────────────────────
        with aioresponses() as m:
            _mock_responses(m, [MOCK_SLOT])
            await coordinator._async_update_data()

        assert hass.services.async_call.await_count == 2
        assert "slot-001" in coordinator.sent_slot_ids

    finally:
        await coordinator._session.close()


# ── test_network_error_preserves_last_state ───────────────────────────────────

@pytest.mark.asyncio
async def test_network_error_preserves_last_state(
    coordinator: RehabDataUpdateCoordinator,
) -> None:
    """A ClientConnectorError must not clear the previous slot count.

    The coordinator returns the last known data with the error field set.
    """
    import aiohttp

    coordinator.data = {  # type: ignore[assignment]
        DATA_TERMINY: [MOCK_SLOT_2],
        DATA_COUNT: 1,
        "ostatnia_aktualizacja": "2025-05-01T09:00:00",
        DATA_ERROR: None,
    }

    coordinator._session = aiohttp.ClientSession()
    try:
        with patch.object(
            coordinator,
            "_fetch_terms",
            side_effect=aiohttp.ClientConnectorError(
                MagicMock(), OSError("connection refused")
            ),
        ):
            data = await coordinator._async_update_data()
    finally:
        await coordinator._session.close()

    # Previous count must be preserved
    assert data[DATA_COUNT] == 1
    assert data[DATA_ERROR] is not None
    assert "Błąd sieci" in data[DATA_ERROR]


# ── test_monitor_inactive_skips_requests ─────────────────────────────────────

@pytest.mark.asyncio
async def test_monitor_inactive_skips_requests(
    coordinator: RehabDataUpdateCoordinator,
) -> None:
    """When monitor_active is False no HTTP requests are sent."""
    coordinator.monitor_active = False

    with aioresponses() as m:
        data = await coordinator._async_update_data()
        assert m.requests == {}

    assert data[DATA_COUNT] == 0

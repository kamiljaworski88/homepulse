# Rehab Monitor — dokumentacja integracji

Integracja dla Home Assistant monitorująca wolne terminy rehabilitacyjne  
w portalu **INTERMEDICUS Centrum Rehabilitacji** (`erj.intermedicus.pl/Portal`).

---

## Spis treści

1. [Wymagania](#wymagania)
2. [Instalacja](#instalacja)
3. [Konfiguracja](#konfiguracja)
4. [Pomocnik (helper)](#pomocnik-helper)
5. [Encje](#encje)
6. [Dashboard (Lovelace)](#dashboard-lovelace)
7. [Jak działa polling](#jak-działa-polling)
8. [Powiadomienia](#powiadomienia)
9. [Rozwiązywanie problemów](#rozwiązywanie-problemów)
10. [Struktura plików](#struktura-plików)

---

## Wymagania

| Element | Wersja minimalna |
|---|---|
| Home Assistant | 2024.1.0 |
| Python | 3.12 |
| `aiohttp` | 3.8 |

Brak zależności z HACS — integracja to czysty custom component.

---

## Instalacja

1. Skopiuj folder `custom_components/rehab_monitor/` do katalogu  
   `<config>/custom_components/` na instancji HA.
2. Zrestartuj Home Assistant.
3. Przejdź do **Ustawienia → Urządzenia i usługi → Dodaj integrację**,  
   wyszukaj „Rehab Monitor" i wypełnij formularz konfiguracji.

---

## Konfiguracja

Formularz konfiguracji (Config Flow) pojawia się przy dodawaniu integracji.  
Wszystkie pola są opcjonalne z wyjątkiem usługi powiadomień.

| Pole | Domyślna wartość | Opis |
|---|---|---|
| **Login** | _(puste)_ | Login do portalu Intermedicus. Zostaw puste, jeśli portal nie wymaga logowania. |
| **Hasło** | _(puste)_ | Hasło do portalu. |
| **Usługa powiadomień** | `notify` | Nazwa usługi HA do wysyłania powiadomień, np. `mobile_app_telefon`. |
| **PlaceId — Terapia dzieci** | `7` | Identyfikator miejsca w API portalu (potwierdzony przez DevTools). |
| **PlaceId — SI-1-1** | `10` | Identyfikator miejsca SI-1-1 w API portalu (potwierdzony przez DevTools). |

> **Jak znaleźć PlaceId?**  
> Otwórz portal w przeglądarce → DevTools (F12) → zakładka Network → wybierz miejsce  
> i kliknij „Szukaj" → znajdź żądanie `FreeTermsFilter` → w payload pola `PlaceId`.

---

## Pomocnik (helper)

Dashboard używa jednego pomocnika, który **trzeba utworzyć ręcznie** w HA:

**Ustawienia → Urządzenia i usługi → Pomocnicy → Dodaj → Przełącznik (input_boolean)**

| Parametr | Wartość |
|---|---|
| Nazwa | `Pokaż harmonogram` |
| Entity ID | `input_boolean.rehab_show_schedule` |
| Stan początkowy | Włączony (opcjonalnie) |

Pomocnik steruje zwijaniem/rozwijaniem sekcji harmonogramu na dashboardzie.

---

## Encje

Po dodaniu integracji tworzone są automatycznie następujące encje:

### Czujniki (tylko do odczytu)

#### `sensor.rehab_wolne_terminy`
- **Stan:** liczba całkowita — ilość dostępnych wolnych terminów (0 gdy brak)
- **Jednostka:** `terminy`
- **Ikona:** `mdi:calendar-check`
- **Atrybuty:**

  | Atrybut | Typ | Opis |
  |---|---|---|
  | `terminy` | lista | Lista wolnych slotów (szczegóły poniżej) |
  | `ostatnia_aktualizacja` | string ISO | Czas ostatniego udanego pobrania |
  | `blad` | string / null | Ostatni błąd lub `null` |

  Każdy element listy `terminy`:
  ```json
  {
    "slot_id": "6312851",
    "data": "2026-04-17",
    "godzina": "14:40",
    "rehabilitant": "Jurek-Pruska Justyna",
    "miejsce": "Terapia Dzieci"
  }
  ```

#### `binary_sensor.rehab_dostepnosc`
- **Stan:** `on` gdy liczba wolnych terminów > 0, `off` w przeciwnym razie
- **Device class:** `occupancy` (wyświetla się jako „Wykryto" / „Czysto")
- Używany przez karty `conditional` na dashboardzie

---

### Przełączniki i kontrolki

#### `switch.rehab_monitor_active`
- Włącza / wyłącza polling HTTP do portalu
- Gdy `off` — żadne żądania nie są wysyłane; koordynator zwraca ostatnie znane dane
- Stan przywracany po restarcie HA (`RestoreEntity`)

#### `select.rehab_miejsce`
- Wybór miejsca do monitorowania
- Opcje: `Terapia dzieci` · `SI-1-1` · `Obie`
- Przy wyborze „Obie" — oba miejsca są odpytywane w każdym cyklu
- Stan przywracany po restarcie HA
- Zmiana opcji wyzwala natychmiastowe odświeżenie

#### `button.rehab_sprawdz_teraz`
- Wyzwala natychmiastowe odpytanie portalu
- **Pomija okno godzinowe** (`_force_refresh = True`) — działa o każdej porze doby

---

### Encje liczbowe (parametry harmonogramu)

Wszystkie encje liczbowe przywracają swój stan po restarcie HA (`RestoreEntity`).

| Encja | Zakres | Domyślnie | Opis |
|---|---|---|---|
| `number.rehab_scan_interval` | 1–60 min | 15 | Interwał automatycznego sprawdzania |
| `number.rehab_hour_start` | 0–22 h | 7 | Od której godziny uruchamiać polling |
| `number.rehab_hour_end` | 1–24 h | 23 | Do której godziny uruchamiać polling |
| `number.rehab_visit_hour_min` | 0–23 h | 0 | Minimalna godzina wizyty (0 = brak filtra) |

> **`rehab_visit_hour_min`:** filtrowanie działa na poziomie koordynatora —  
> sloty z godziną wcześniejszą niż ustawiona wartość są odrzucane przed zapisem  
> i **nie generują powiadomień**. Wartość `0` wyłącza filtr.

---

## Dashboard (Lovelace)

Plik konfiguracyjny dashboardu: `lovelace_rehab.yaml`

### Wgranie do HA

**Opcja A — Raw Config Editor:**  
Otwórz widok → ⋮ → Edytuj pulpit → Raw Config Editor → wklej zawartość pliku.

**Opcja B — plik w konfiguracji HA:**  
W `ui-lovelace.yaml` (lub przez Zarządzanie pulpitem → Dodaj widok z pliku YAML).

### Struktura dashboardu

```
Rehab Monitor
├── Nagłówek (ikona + tytuł)
├── Glance: Dostępność · Wolne terminy
├── Kontrolki: Monitorowanie włączone · Szukaj miejsca · Sprawdź teraz
├── Harmonogram [zwijany ▲/▼]
│   ├── Podsumowanie: ⏱ co X min · HH:00–HH:00
│   ├── Interwał (min)
│   ├── Sprawdzaj od (godz.)
│   ├── Sprawdzaj do (godz.)
│   └── Pokaż wizyty od (godz.)
├── Lista terminów [widoczna gdy binary_sensor = on]
│   └── Karty z datą, godziną, rehabilitantem, miejscem
└── Brak terminów / Błąd [widoczna gdy binary_sensor = off]
    └── Informacja o ostatnim sprawdzeniu
```

---

## Jak działa polling

```
HA timer tick
    │
    ├─ monitor_active == off?  → zwróć ostatnie dane (brak żądań HTTP)
    │
    ├─ _is_active_hours() == False i force_refresh == False?  → j.w.
    │
    └─ Wykonaj cykl:
         1. GET /Portal/Terms  →  pobierz CSRF token z HTML
         2. POST /Portal/Terms/FreeTermsFilter  (form-urlencoded)
              PlaceId, DateFrom, DateTo, __RequestVerificationToken, …
         3. POST /Portal/Terms/GetFreeTerms  (form-urlencoded)
              sort=&page=1&pageSize=20&group=&filter=&__RequestVerificationToken=…
         4. Parsuj JSON {"Data": [...], "Total": n}
         5. Odfiltruj IsBooked == true i godziny < visit_hour_min
         6. Wyślij powiadomienia dla nowych slot_id
         7. Zaktualizuj sensor / binary_sensor
```

**Obsługa sesji i CSRF:**
- Token `__RequestVerificationToken` jest ekstrahelowany z HTML strony portalu regexem
- Przy błędzie HTTP 400/401/403 token jest odświeżany automatycznie i żądanie powtarzane
- Sesja (`aiohttp.CookieJar`) jest współdzielona przez cały czas życia integracji
- SSL jest wyłączony (`ssl=False`) — certyfikat portalu nie przechodzi weryfikacji łańcucha CA,  
  ale połączenie jest nadal szyfrowane (HTTPS)

**Deduplikacja powiadomień:**
- Zestaw `sent_slot_ids` przechowuje ID slotów, dla których powiadomienie już wysłano
- Sloty, które zniknęły z API (ktoś zarezerwował), są usuwane ze zbioru —  
  jeśli termin pojawi się ponownie (anulowanie rezerwacji), wygeneruje nowe powiadomienie

---

## Powiadomienia

Powiadomienie jest wysyłane przez `hass.services.async_call("notify", <usługa>, ...)`.

Przykładowy format wiadomości:
```
Tytuł: Wolny termin rehabilitacji!
Treść:
  📅 2026-04-17 14:40
  👤 Jurek-Pruska Justyna
  🏥 Terapia Dzieci
```

Usługę powiadomień ustawiasz w konfiguracji integracji (np. `mobile_app_moj_telefon`).  
Możliwe wartości: dowolna usługa z domeny `notify` zarejestrowana w HA.

---

## Rozwiązywanie problemów

### Integracja dodaje się poprawnie, ale nie ma wyników

1. Sprawdź `switch.rehab_monitor_active` — czy jest włączony.
2. Sprawdź czy aktualny czas mieści się w oknie `rehab_hour_start`–`rehab_hour_end`.
3. Kliknij `button.rehab_sprawdz_teraz` — wymusza sprawdzenie poza oknem godzinowym.
4. Sprawdź atrybut `blad` w `sensor.rehab_wolne_terminy` (Narzędzia deweloperskie → Stany).

### Błąd „Nieprawidłowa odpowiedź serwera (HTML zamiast JSON)"

Sesja HTTP wygasła lub portal przekierował na stronę logowania.  
Integracja automatycznie odświeża token CSRF i ponawia żądanie przy kolejnym ticku.  
Jeśli błąd się powtarza — sprawdź dane logowania w konfiguracji integracji.

### Błąd „Błąd sieci" lub „Przekroczono czas oczekiwania"

Portal jest niedostępny lub instancja HA nie ma dostępu do internetu.  
Integracja zachowuje ostatnie znane dane i ponowi próbę przy kolejnym ticku.

### Zmiana interwału nie działa od razu

Zmiana wartości `number.rehab_scan_interval` odwołuje bieżący timer i planuje nowy  
natychmiast — nowy interwał wchodzi w życie od razu, bez czekania na koniec bieżącego cyklu.

### Dashboard nie wyświetla sekcji harmonogramu

Upewnij się, że pomocnik `input_boolean.rehab_show_schedule` istnieje w HA  
(Ustawienia → Pomocnicy). Bez tego encja karty `conditional` nie może się przełączać.

---

## Struktura plików

```
custom_components/rehab_monitor/
├── __init__.py          – setup / unload entry
├── manifest.json        – metadane integracji (wersja, wymagania, iot_class)
├── const.py             – wszystkie stałe: URL, nazwy pól API, klucze danych
├── coordinator.py       – logika pollingu, parsowania, powiadomień
├── config_flow.py       – formularz konfiguracji (UI)
├── switch.py            – switch.rehab_monitor_active
├── select.py            – select.rehab_miejsce
├── sensor.py            – sensor.rehab_wolne_terminy
├── binary_sensor.py     – binary_sensor.rehab_dostepnosc
├── button.py            – button.rehab_sprawdz_teraz
└── number.py            – number.rehab_scan_interval / hour_start / hour_end / visit_hour_min

lovelace_rehab.yaml      – konfiguracja dashboardu
docs/rehab_monitor.md    – ten plik
```

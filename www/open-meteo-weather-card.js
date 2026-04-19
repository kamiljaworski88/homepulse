/**
 * Open-Meteo Weather Card — nowoczesna karta pogodowa dla Home Assistant
 *
 * Użycie w dashboardzie:
 *   type: custom:open-meteo-weather-card
 *   entity: weather.moja_pogoda                 # wymagane
 *   sensor_current: sensor.moja_pogoda_current  # opcjonalne
 *   sensor_daily:   sensor.moja_pogoda_daily    # opcjonalne
 *   sensor_hourly:  sensor.moja_pogoda_hourly   # opcjonalne
 *   name: "Moja Pogoda"                         # opcjonalne
 */

// ── WMO weather code → emoji + label PL ──────────────────────────────────────
const WMO = {
  0:  { icon: "☀️",  label: "Słonecznie" },
  1:  { icon: "🌤️", label: "Głównie słonecznie" },
  2:  { icon: "⛅",  label: "Częściowe zachmurzenie" },
  3:  { icon: "☁️",  label: "Pochmurno" },
  45: { icon: "🌫️", label: "Mgła" },
  48: { icon: "🌫️", label: "Mgła osadzająca szron" },
  51: { icon: "🌦️", label: "Mżawka słaba" },
  53: { icon: "🌦️", label: "Mżawka" },
  55: { icon: "🌧️", label: "Mżawka silna" },
  56: { icon: "🌨️", label: "Marznąca mżawka" },
  57: { icon: "🌨️", label: "Marznąca mżawka silna" },
  61: { icon: "🌧️", label: "Deszcz słaby" },
  63: { icon: "🌧️", label: "Deszcz" },
  65: { icon: "🌧️", label: "Deszcz silny" },
  66: { icon: "🌨️", label: "Marznący deszcz" },
  67: { icon: "🌨️", label: "Marznący deszcz silny" },
  71: { icon: "🌨️", label: "Śnieg słaby" },
  73: { icon: "❄️",  label: "Śnieg" },
  75: { icon: "❄️",  label: "Śnieg silny" },
  77: { icon: "🌨️", label: "Ziarna śnieżne" },
  80: { icon: "🌦️", label: "Przelotne opady" },
  81: { icon: "🌧️", label: "Przelotne opady" },
  82: { icon: "⛈️",  label: "Gwałtowne opady" },
  85: { icon: "🌨️", label: "Przelotny śnieg" },
  86: { icon: "❄️",  label: "Przelotny śnieg silny" },
  95: { icon: "⛈️",  label: "Burza" },
  96: { icon: "⛈️",  label: "Burza z gradem" },
  99: { icon: "⛈️",  label: "Burza z gradem silna" },
};

// Gradient tła zależny od kondycji + pora dnia
const BG_GRADIENTS = {
  sunny:          "linear-gradient(135deg, #1a6fc4 0%, #48b5f0 50%, #f5a623 100%)",
  "clear-night":  "linear-gradient(135deg, #0a0e2e 0%, #1a2a6c 50%, #2d3561 100%)",
  partlycloudy:   "linear-gradient(135deg, #1e6bb8 0%, #5a9fd4 60%, #aac8e4 100%)",
  cloudy:         "linear-gradient(135deg, #4a5568 0%, #718096 60%, #a0aec0 100%)",
  fog:            "linear-gradient(135deg, #6b7280 0%, #9ca3af 60%, #d1d5db 100%)",
  rainy:          "linear-gradient(135deg, #1e3a5f 0%, #2d5986 50%, #4a7fa5 100%)",
  snowy:          "linear-gradient(135deg, #3b6cb7 0%, #7bafd4 50%, #dce8f5 100%)",
  "lightning-rainy": "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
  exceptional:    "linear-gradient(135deg, #4a1942 0%, #7b2d8b 50%, #b45aad 100%)",
};

function conditionGradient(condition) {
  return BG_GRADIENTS[condition] ?? BG_GRADIENTS.sunny;
}

function conditionEmoji(condition, code) {
  if (code !== undefined && WMO[code]) return WMO[code].icon;
  const map = {
    sunny: "☀️", "clear-night": "🌙", partlycloudy: "⛅", cloudy: "☁️",
    fog: "🌫️", rainy: "🌧️", snowy: "❄️", "lightning-rainy": "⛈️", exceptional: "🌀",
  };
  return map[condition] ?? "🌡️";
}

function windDirLabel(deg) {
  const dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"];
  return dirs[Math.round(((deg % 360) + 360) % 360 / 22.5) % 16];
}

function dayLabel(dateStr) {
  const d = new Date(dateStr);
  const days = ["Nie","Pon","Wt","Śr","Czw","Pt","Sob"];
  const today = new Date();
  const diff = Math.round((d - new Date(today.toDateString())) / 86400000);
  if (diff === 0) return "Dziś";
  if (diff === 1) return "Jutro";
  return days[d.getDay()];
}

function hourLabel(dateStr) {
  return new Date(dateStr).toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" });
}

// ── Styles ────────────────────────────────────────────────────────────────────
const STYLES = `
  :host { display: block; font-family: var(--primary-font-family, sans-serif); }

  .card {
    border-radius: 24px;
    overflow: hidden;
    color: #fff;
    position: relative;
    box-shadow: 0 8px 32px rgba(0,0,0,.35);
    transition: background .8s ease;
  }

  /* ── Hero (górna sekcja) ── */
  .hero {
    padding: 28px 24px 20px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    position: relative;
  }

  .hero-left { flex: 1; }

  .location {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: .12em;
    text-transform: uppercase;
    opacity: .75;
    margin-bottom: 4px;
  }

  .temp-row {
    display: flex;
    align-items: flex-start;
    gap: 4px;
    line-height: 1;
  }

  .temp-main {
    font-size: 80px;
    font-weight: 200;
    letter-spacing: -4px;
    text-shadow: 0 2px 16px rgba(0,0,0,.25);
  }

  .temp-unit {
    font-size: 28px;
    font-weight: 300;
    margin-top: 14px;
    opacity: .85;
  }

  .feels-like {
    font-size: 13px;
    opacity: .7;
    margin-top: 4px;
  }

  .condition-label {
    font-size: 17px;
    font-weight: 500;
    margin-top: 8px;
    text-shadow: 0 1px 8px rgba(0,0,0,.2);
  }

  .hero-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
  }

  .big-icon {
    font-size: 72px;
    line-height: 1;
    filter: drop-shadow(0 4px 12px rgba(0,0,0,.3));
    animation: float 4s ease-in-out infinite;
  }

  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-6px); }
  }

  .updated {
    font-size: 11px;
    opacity: .55;
    margin-top: 2px;
  }

  /* ── Pasek statystyk ── */
  .stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: rgba(255,255,255,.12);
    border-top: 1px solid rgba(255,255,255,.12);
    border-bottom: 1px solid rgba(255,255,255,.12);
  }

  .stat {
    padding: 12px 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    background: rgba(0,0,0,.12);
    backdrop-filter: blur(4px);
    transition: background .2s;
  }

  .stat:hover { background: rgba(255,255,255,.08); }

  .stat-icon { font-size: 18px; }
  .stat-value { font-size: 15px; font-weight: 600; }
  .stat-label { font-size: 10px; opacity: .65; letter-spacing: .05em; text-transform: uppercase; }

  /* ── Prognoza godzinowa ── */
  .section-title {
    padding: 14px 20px 8px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
    opacity: .6;
  }

  .hourly-scroll {
    display: flex;
    gap: 0;
    overflow-x: auto;
    padding: 0 16px 12px;
    scrollbar-width: none;
  }
  .hourly-scroll::-webkit-scrollbar { display: none; }

  .hour-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
    min-width: 56px;
    padding: 10px 4px;
    border-radius: 14px;
    transition: background .2s;
    cursor: default;
  }

  .hour-item:hover { background: rgba(255,255,255,.12); }

  .hour-item.now {
    background: rgba(255,255,255,.18);
    box-shadow: 0 0 0 1px rgba(255,255,255,.3);
  }

  .hour-time { font-size: 11px; opacity: .7; font-weight: 500; }
  .hour-icon { font-size: 20px; }
  .hour-temp { font-size: 13px; font-weight: 600; }
  .hour-precip { font-size: 10px; opacity: .65; }

  /* ── Prognoza dzienna ── */
  .daily-list {
    padding: 0 16px 20px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .day-row {
    display: grid;
    grid-template-columns: 52px 28px 1fr auto auto;
    align-items: center;
    gap: 10px;
    padding: 9px 12px;
    border-radius: 14px;
    transition: background .2s;
  }

  .day-row:hover { background: rgba(255,255,255,.1); }

  .day-name { font-size: 14px; font-weight: 500; }
  .day-icon { font-size: 20px; text-align: center; }

  .precip-bar-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .precip-pct { font-size: 11px; opacity: .6; width: 28px; text-align: right; }

  .bar-track {
    flex: 1;
    height: 4px;
    border-radius: 2px;
    background: rgba(255,255,255,.2);
    overflow: hidden;
  }

  .bar-fill {
    height: 100%;
    border-radius: 2px;
    background: rgba(120,200,255,.8);
  }

  .day-tmin { font-size: 13px; opacity: .6; min-width: 36px; text-align: right; }
  .day-tmax { font-size: 14px; font-weight: 600; min-width: 36px; text-align: right; }

  /* ── Wschód / zachód słońca ── */
  .sun-row {
    display: flex;
    justify-content: space-around;
    padding: 12px 24px 20px;
    border-top: 1px solid rgba(255,255,255,.1);
    margin-top: 4px;
  }

  .sun-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
  }

  .sun-icon { font-size: 22px; }
  .sun-time { font-size: 15px; font-weight: 600; }
  .sun-lbl  { font-size: 10px; opacity: .6; text-transform: uppercase; letter-spacing: .08em; }
`;

// ── Card component ────────────────────────────────────────────────────────────
class OpenMeteoWeatherCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    if (!config.entity) throw new Error("Podaj entity: weather.brzeziny");
    this._config = {
      entity: config.entity,
      name: config.name ?? "Pogoda",
      sensor_current: config.sensor_current ?? null,
      sensor_daily:   config.sensor_daily   ?? null,
      sensor_hourly:  config.sensor_hourly  ?? null,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _attr(entityId, key) {
    if (!entityId || !this._hass.states[entityId]) return null;
    return this._hass.states[entityId].attributes[key] ?? null;
  }

  _render() {
    const hass = this._hass;
    const cfg  = this._config;
    const ws   = hass.states[cfg.entity];
    if (!ws) {
      this.shadowRoot.innerHTML = `<ha-card><div style="padding:16px;color:red">Encja ${cfg.entity} nie znaleziona.</div></ha-card>`;
      return;
    }

    const attrs     = ws.attributes;
    const condition = ws.state;
    const gradient  = conditionGradient(condition);

    // Dane bieżące
    const code      = this._attr(cfg.sensor_current, "weather_code");
    const mainIcon  = conditionEmoji(condition, code);
    const temp      = this._attr(cfg.sensor_current, "temperature_2m") ?? attrs.temperature ?? "--";
    const feelsLike = this._attr(cfg.sensor_current, "apparent_temperature") ?? "--";
    const humidity  = this._attr(cfg.sensor_current, "relative_humidity_2m") ?? attrs.humidity ?? "--";
    const pressure  = this._attr(cfg.sensor_current, "pressure_msl") ?? attrs.pressure ?? "--";
    const windSpd   = this._attr(cfg.sensor_current, "wind_speed_10m") ?? attrs.wind_speed ?? "--";
    const windDir   = this._attr(cfg.sensor_current, "wind_direction_10m") ?? attrs.wind_bearing ?? null;
    const windGusts = this._attr(cfg.sensor_current, "wind_gusts_10m") ?? "--";
    const cloudCov  = this._attr(cfg.sensor_current, "cloud_cover") ?? "--";
    const condLabel = code != null && WMO[code] ? WMO[code].label : condition;
    const updTime   = this._attr(cfg.sensor_current, "time")
      ? new Date(this._attr(cfg.sensor_current, "time")).toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" })
      : "";

    const windDirStr = windDir != null ? `${windDirLabel(windDir)} ${Math.round(windDir)}°` : "--";

    // Wschód / zachód słońca z daily[0]
    const sunriseArr = this._attr(cfg.sensor_daily, "sunrise");
    const sunsetArr  = this._attr(cfg.sensor_daily, "sunset");
    const sunriseStr = sunriseArr ? new Date(sunriseArr[0]).toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" }) : "--:--";
    const sunsetStr  = sunsetArr  ? new Date(sunsetArr[0]).toLocaleTimeString("pl-PL",  { hour: "2-digit", minute: "2-digit" }) : "--:--";

    // Prognoza dzienna z weather entity lub sensor_daily
    const dailyForecast = this._buildDailyForecast(attrs);

    // Prognoza godzinowa
    const hourlyForecast = this._buildHourlyForecast(attrs);

    this.shadowRoot.innerHTML = `
      <style>${STYLES}</style>
      <div class="card" style="background:${gradient}">

        <!-- HERO -->
        <div class="hero">
          <div class="hero-left">
            <div class="location">${cfg.name}</div>
            <div class="temp-row">
              <span class="temp-main">${Math.round(temp)}</span>
              <span class="temp-unit">°C</span>
            </div>
            <div class="feels-like">Odczuwalna ${Math.round(feelsLike)}°C</div>
            <div class="condition-label">${condLabel}</div>
          </div>
          <div class="hero-right">
            <div class="big-icon">${mainIcon}</div>
            ${updTime ? `<div class="updated">akt. ${updTime}</div>` : ""}
          </div>
        </div>

        <!-- STATS -->
        <div class="stats">
          ${this._statHTML("💧", `${humidity}%`, "Wilgotność")}
          ${this._statHTML("🌬️", `${windSpd} km/h`, `Wiatr ${windDirStr}`)}
          ${this._statHTML("💨", `${windGusts} km/h`, "Porywy")}
          ${this._statHTML("🌡️", `${pressure} hPa`, "Ciśnienie")}
          ${this._statHTML("☁️", `${cloudCov}%`, "Zachmurzenie")}
          ${this._statHTML("🌅", `${sunriseStr} / ${sunsetStr}`, "Wschód / Zachód")}
        </div>

        <!-- GODZINOWA -->
        ${hourlyForecast.length ? `
          <div class="section-title">Prognoza godzinowa</div>
          <div class="hourly-scroll">
            ${hourlyForecast.map((h, i) => this._hourHTML(h, i === 0)).join("")}
          </div>
        ` : ""}

        <!-- DZIENNA -->
        ${dailyForecast.length ? `
          <div class="section-title">Prognoza 7-dniowa</div>
          <div class="daily-list">
            ${dailyForecast.map(d => this._dayHTML(d)).join("")}
          </div>
        ` : ""}

        <!-- WSCHÓD / ZACHÓD (duży) -->
        <div class="sun-row">
          <div class="sun-item">
            <span class="sun-icon">🌅</span>
            <span class="sun-time">${sunriseStr}</span>
            <span class="sun-lbl">Wschód</span>
          </div>
          <div class="sun-item">
            <span class="sun-icon">🌇</span>
            <span class="sun-time">${sunsetStr}</span>
            <span class="sun-lbl">Zachód</span>
          </div>
        </div>

      </div>
    `;
  }

  _statHTML(icon, value, label) {
    return `
      <div class="stat">
        <span class="stat-icon">${icon}</span>
        <span class="stat-value">${value}</span>
        <span class="stat-label">${label}</span>
      </div>`;
  }

  _hourHTML(h, isNow) {
    const pct = h.precipitation_probability ?? 0;
    return `
      <div class="hour-item ${isNow ? "now" : ""}">
        <span class="hour-time">${isNow ? "Teraz" : hourLabel(h.datetime)}</span>
        <span class="hour-icon">${conditionEmoji(h.condition)}</span>
        <span class="hour-temp">${Math.round(h.temperature)}°</span>
        <span class="hour-precip">${pct > 0 ? pct + "%" : ""}</span>
      </div>`;
  }

  _dayHTML(d) {
    const pct = d.precipitation_probability ?? 0;
    return `
      <div class="day-row">
        <span class="day-name">${dayLabel(d.datetime)}</span>
        <span class="day-icon">${conditionEmoji(d.condition)}</span>
        <div class="precip-bar-wrap">
          <span class="precip-pct">${pct > 0 ? pct + "%" : ""}</span>
          <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>
        </div>
        <span class="day-tmin">${Math.round(d.templow ?? d.temperature_min ?? 0)}°</span>
        <span class="day-tmax">${Math.round(d.temperature ?? d.temperature_max ?? 0)}°</span>
      </div>`;
  }

  // Pobiera prognozę dzienną z encji weather lub z sensor_daily
  _buildDailyForecast(weatherAttrs) {
    // HA 2024.3+ trzyma forecast jako atrybut forecast
    const raw = weatherAttrs.forecast;
    if (Array.isArray(raw) && raw.length) return raw.slice(0, 7);

    // Fallback: sensor_daily
    const times   = this._attr(this._config.sensor_daily, "time");
    const tmax    = this._attr(this._config.sensor_daily, "temperature_2m_max");
    const tmin    = this._attr(this._config.sensor_daily, "temperature_2m_min");
    const codes   = this._attr(this._config.sensor_daily, "weather_code");
    const precip  = this._attr(this._config.sensor_daily, "precipitation_sum");
    const pprob   = this._attr(this._config.sensor_daily, "precipitation_probability_max");
    const wind    = this._attr(this._config.sensor_daily, "wind_speed_10m_max");
    const wdir    = this._attr(this._config.sensor_daily, "wind_direction_10m_dominant");

    if (!times) return [];
    return times.map((t, i) => {
      const c = codes?.[i] ?? 0;
      return {
        datetime: t,
        condition: this._wmoToCondition(c),
        temperature: tmax?.[i] ?? 0,
        templow: tmin?.[i] ?? 0,
        precipitation: precip?.[i] ?? 0,
        precipitation_probability: pprob?.[i] ?? 0,
        wind_speed: wind?.[i] ?? 0,
        wind_bearing: wdir?.[i] ?? 0,
      };
    }).slice(0, 7);
  }

  // Pobiera prognozę godzinową z encji weather lub sensor_hourly
  _buildHourlyForecast(weatherAttrs) {
    const raw = weatherAttrs.hourly_forecast ?? weatherAttrs.forecast_hourly;
    if (Array.isArray(raw) && raw.length) return raw.slice(0, 24);

    const times  = this._attr(this._config.sensor_hourly, "time");
    const temp   = this._attr(this._config.sensor_hourly, "temperature_2m");
    const codes  = this._attr(this._config.sensor_hourly, "weather_code");
    const precip = this._attr(this._config.sensor_hourly, "precipitation");
    const pprob  = this._attr(this._config.sensor_hourly, "precipitation_probability");
    const isday  = this._attr(this._config.sensor_hourly, "is_day");

    if (!times) return [];
    const now = Date.now();
    return times
      .map((t, i) => ({
        datetime: t,
        condition: this._wmoToCondition(codes?.[i] ?? 0, isday?.[i] ?? 1),
        temperature: temp?.[i] ?? 0,
        precipitation: precip?.[i] ?? 0,
        precipitation_probability: pprob?.[i] ?? 0,
      }))
      .filter(h => new Date(h.datetime).getTime() >= now - 1800000)
      .slice(0, 24);
  }

  _wmoToCondition(code, isDay = 1) {
    if (code === 0) return isDay ? "sunny" : "clear-night";
    if ([1, 2].includes(code)) return "partlycloudy";
    if (code === 3) return "cloudy";
    if ([45, 48].includes(code)) return "fog";
    if ([51,53,55,56,57,61,63,65,66,67,80,81,82].includes(code)) return "rainy";
    if ([71,73,75,77,85,86].includes(code)) return "snowy";
    if ([95,96,99].includes(code)) return "lightning-rainy";
    return "exceptional";
  }

  static getConfigElement() {
    return document.createElement("brzeziny-weather-card-editor");
  }

  static getStubConfig() {
    return {
      entity: "weather.moja_pogoda",
      name: "Moja Pogoda",
      sensor_current: "sensor.moja_pogoda_current",
      sensor_daily:   "sensor.moja_pogoda_daily",
      sensor_hourly:  "sensor.moja_pogoda_hourly",
    };
  }
}

customElements.define("open-meteo-weather-card", OpenMeteoWeatherCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "open-meteo-weather-card",
  name: "Open-Meteo Weather Card",
  description: "Nowoczesna karta pogodowa (Open-Meteo)",
  preview: true,
});

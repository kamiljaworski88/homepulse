/**
 * Open-Meteo Weather Card
 * Nowoczesna karta pogodowa — auto-rejestrowana przez integrację Open-Meteo Weather
 *
 * Użycie:
 *   type: custom:open-meteo-weather-card
 *   entity: weather.moja_pogoda
 *   name: "Moja Pogoda"   # opcjonalne — nadpisuje nazwę encji
 */

const WMO_ICONS = {
  0:"☀️", 1:"🌤️", 2:"⛅", 3:"☁️",
  45:"🌫️", 48:"🌫️",
  51:"🌦️", 53:"🌦️", 55:"🌧️", 56:"🌨️", 57:"🌨️",
  61:"🌧️", 63:"🌧️", 65:"🌧️", 66:"🌨️", 67:"🌨️",
  71:"🌨️", 73:"❄️", 75:"❄️", 77:"🌨️",
  80:"🌦️", 81:"🌧️", 82:"⛈️",
  85:"🌨️", 86:"❄️",
  95:"⛈️", 96:"⛈️", 99:"⛈️",
};

const COND_GRADIENTS = {
  sunny:            "linear-gradient(135deg,#1a6fc4 0%,#48b5f0 50%,#f5a623 100%)",
  "clear-night":    "linear-gradient(135deg,#0a0e2e 0%,#1a2a6c 50%,#2d3561 100%)",
  partlycloudy:     "linear-gradient(135deg,#1e6bb8 0%,#5a9fd4 60%,#aac8e4 100%)",
  cloudy:           "linear-gradient(135deg,#4a5568 0%,#718096 60%,#a0aec0 100%)",
  fog:              "linear-gradient(135deg,#6b7280 0%,#9ca3af 60%,#d1d5db 100%)",
  rainy:            "linear-gradient(135deg,#1e3a5f 0%,#2d5986 50%,#4a7fa5 100%)",
  snowy:            "linear-gradient(135deg,#3b6cb7 0%,#7bafd4 50%,#dce8f5 100%)",
  "lightning-rainy":"linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%)",
  exceptional:      "linear-gradient(135deg,#4a1942 0%,#7b2d8b 50%,#b45aad 100%)",
};

const COND_EMOJI = {
  sunny:"☀️","clear-night":"🌙",partlycloudy:"⛅",cloudy:"☁️",
  fog:"🌫️",rainy:"🌧️",snowy:"❄️","lightning-rainy":"⛈️",exceptional:"🌀",
};

function condIcon(condition, code) {
  if (code != null && WMO_ICONS[code]) return WMO_ICONS[code];
  return COND_EMOJI[condition] ?? "🌡️";
}

function windLabel(deg) {
  const d = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"];
  return d[Math.round(((+deg % 360) + 360) % 360 / 22.5) % 16];
}

function dayLabel(iso) {
  const d = new Date(iso), t = new Date();
  const diff = Math.round((d - new Date(t.toDateString())) / 86400000);
  if (diff === 0) return "Dziś";
  if (diff === 1) return "Jutro";
  return ["Nie","Pon","Wt","Śr","Czw","Pt","Sob"][d.getDay()];
}

function hourLabel(iso) {
  return new Date(iso).toLocaleTimeString("pl-PL", { hour:"2-digit", minute:"2-digit" });
}

function sunTime(iso) {
  if (!iso) return "--:--";
  try { return new Date(iso).toLocaleTimeString("pl-PL", { hour:"2-digit", minute:"2-digit" }); }
  catch { return "--:--"; }
}

// ── Styles ────────────────────────────────────────────────────────────────────
const CSS = `
:host { display: block; }

.card {
  border-radius: 24px;
  overflow: hidden;
  color: #fff;
  box-shadow: 0 8px 32px rgba(0,0,0,.35);
}

/* Hero */
.hero {
  padding: 28px 24px 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.hero-left { flex: 1; min-width: 0; }

.location {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
  opacity: .7;
  margin-bottom: 4px;
}

.temp-row { display: flex; align-items: flex-start; gap: 2px; line-height: 1; }
.temp-main { font-size: 80px; font-weight: 200; letter-spacing: -4px; text-shadow: 0 2px 16px rgba(0,0,0,.25); }
.temp-unit { font-size: 26px; font-weight: 300; margin-top: 14px; opacity: .85; }
.feels    { font-size: 13px; opacity: .65; margin-top: 4px; }
.cond-lbl { font-size: 17px; font-weight: 500; margin-top: 8px; }

.hero-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}
.big-icon {
  font-size: 72px;
  line-height: 1;
  filter: drop-shadow(0 4px 12px rgba(0,0,0,.3));
  animation: float 4s ease-in-out infinite;
}
@keyframes float {
  0%,100% { transform: translateY(0); }
  50%      { transform: translateY(-6px); }
}
.updated { font-size: 11px; opacity: .5; }

/* Stats grid */
.stats {
  display: grid;
  grid-template-columns: repeat(3,1fr);
  gap: 1px;
  background: rgba(255,255,255,.12);
  border-top: 1px solid rgba(255,255,255,.12);
  border-bottom: 1px solid rgba(255,255,255,.12);
}
.stat {
  padding: 11px 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  background: rgba(0,0,0,.12);
  backdrop-filter: blur(4px);
  transition: background .2s;
}
.stat:hover { background: rgba(255,255,255,.08); }
.stat-icon  { font-size: 17px; }
.stat-val   { font-size: 14px; font-weight: 600; }
.stat-lbl   { font-size: 10px; opacity: .6; letter-spacing: .04em; text-transform: uppercase; text-align: center; }

/* Section title */
.sec {
  padding: 13px 20px 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
  opacity: .55;
}

/* Hourly */
.hourly {
  display: flex;
  overflow-x: auto;
  padding: 0 16px 12px;
  scrollbar-width: none;
  gap: 2px;
}
.hourly::-webkit-scrollbar { display: none; }
.h-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 54px;
  padding: 9px 4px;
  border-radius: 12px;
  transition: background .2s;
  flex-shrink: 0;
}
.h-item:hover { background: rgba(255,255,255,.1); }
.h-item.now {
  background: rgba(255,255,255,.18);
  box-shadow: 0 0 0 1px rgba(255,255,255,.28);
}
.h-time  { font-size: 11px; opacity: .65; font-weight: 500; }
.h-icon  { font-size: 19px; }
.h-temp  { font-size: 13px; font-weight: 600; }
.h-rain  { font-size: 10px; opacity: .6; }

/* Daily */
.daily { padding: 0 16px 18px; display: flex; flex-direction: column; gap: 3px; }
.d-row {
  display: grid;
  grid-template-columns: 50px 26px 1fr 38px 38px;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 12px;
  transition: background .2s;
}
.d-row:hover { background: rgba(255,255,255,.09); }
.d-name { font-size: 14px; font-weight: 500; }
.d-icon { font-size: 19px; text-align: center; }
.d-bar-wrap { display: flex; align-items: center; gap: 5px; }
.d-pct  { font-size: 11px; opacity: .55; min-width: 28px; text-align: right; }
.bar    { flex: 1; height: 4px; border-radius: 2px; background: rgba(255,255,255,.18); overflow: hidden; }
.bar-f  { height: 100%; border-radius: 2px; background: rgba(120,200,255,.8); }
.d-lo   { font-size: 13px; opacity: .55; text-align: right; }
.d-hi   { font-size: 14px; font-weight: 600; text-align: right; }

/* Sun row */
.sun {
  display: flex;
  justify-content: space-around;
  padding: 10px 24px 20px;
  border-top: 1px solid rgba(255,255,255,.1);
  margin-top: 2px;
}
.sun-item { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.sun-ico  { font-size: 20px; }
.sun-t    { font-size: 15px; font-weight: 600; }
.sun-l    { font-size: 10px; opacity: .55; text-transform: uppercase; letter-spacing: .07em; }
`;

// ── Component ─────────────────────────────────────────────────────────────────
class OpenMeteoWeatherCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    if (!config.entity) throw new Error("Wymagane pole: entity");
    this._config = { name: null, ...config };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    const { entity, name } = this._config;
    const ws = this._hass.states[entity];
    if (!ws) {
      this.shadowRoot.innerHTML = `<div style="padding:16px;color:var(--error-color,red)">Encja ${entity} nie znaleziona.</div>`;
      return;
    }

    const a        = ws.attributes;
    const cond     = ws.state;
    const gradient = COND_GRADIENTS[cond] ?? COND_GRADIENTS.sunny;
    const code     = a.weather_code ?? null;
    const label    = a.weather_label || cond;
    const mainIcon = condIcon(cond, code);

    const temp      = a.temperature ?? "--";
    const feels     = a.feels_like  ?? "--";
    const humidity  = a.humidity    ?? "--";
    const pressure  = a.pressure    ?? "--";
    const windSpd   = a.wind_speed  ?? "--";
    const windDir   = a.wind_bearing ?? null;
    const windGusts = a.wind_gusts  ?? "--";
    const cloud     = a.cloud_cover ?? "--";
    const uv        = a.uv_index_max ?? "--";
    const windStr   = windDir != null ? `${windLabel(windDir)} ${Math.round(windDir)}°` : "--";

    const updAt   = a.updated_at ? new Date(a.updated_at).toLocaleTimeString("pl-PL", { hour:"2-digit", minute:"2-digit" }) : "";
    const sunrise = sunTime(a.sunrise);
    const sunset  = sunTime(a.sunset);

    const locationName = name || a.friendly_name || entity;
    const daily  = Array.isArray(a.forecast_daily)  ? a.forecast_daily  : [];
    const hourly = Array.isArray(a.forecast_hourly) ? a.forecast_hourly : [];

    this.shadowRoot.innerHTML = `
      <style>${CSS}</style>
      <div class="card" style="background:${gradient}">

        <div class="hero">
          <div class="hero-left">
            <div class="location">${locationName}</div>
            <div class="temp-row">
              <span class="temp-main">${isNaN(+temp) ? temp : Math.round(+temp)}</span>
              <span class="temp-unit">°C</span>
            </div>
            <div class="feels">Odczuwalna ${isNaN(+feels) ? feels : Math.round(+feels)}°C</div>
            <div class="cond-lbl">${label}</div>
          </div>
          <div class="hero-right">
            <div class="big-icon">${mainIcon}</div>
            ${updAt ? `<div class="updated">akt. ${updAt}</div>` : ""}
          </div>
        </div>

        <div class="stats">
          ${this._stat("💧", `${humidity}%`, "Wilgotność")}
          ${this._stat("🌬️", `${windSpd} km/h`, `Wiatr ${windStr}`)}
          ${this._stat("💨", `${windGusts} km/h`, "Porywy")}
          ${this._stat("🌡️", `${pressure} hPa`, "Ciśnienie")}
          ${this._stat("☁️", `${cloud}%`, "Zachmurzenie")}
          ${this._stat("🔆", `${uv}`, "UV max")}
        </div>

        ${hourly.length ? `
          <div class="sec">Prognoza godzinowa</div>
          <div class="hourly">
            ${hourly.map((h,i) => this._hour(h, i===0)).join("")}
          </div>` : ""}

        ${daily.length ? `
          <div class="sec">Prognoza 7-dniowa</div>
          <div class="daily">
            ${daily.map(d => this._day(d)).join("")}
          </div>` : ""}

        <div class="sun">
          <div class="sun-item">
            <span class="sun-ico">🌅</span>
            <span class="sun-t">${sunrise}</span>
            <span class="sun-l">Wschód</span>
          </div>
          <div class="sun-item">
            <span class="sun-ico">🌇</span>
            <span class="sun-t">${sunset}</span>
            <span class="sun-l">Zachód</span>
          </div>
        </div>

      </div>`;
  }

  _stat(icon, value, label) {
    return `<div class="stat">
      <span class="stat-icon">${icon}</span>
      <span class="stat-val">${value}</span>
      <span class="stat-lbl">${label}</span>
    </div>`;
  }

  _hour(h, isNow) {
    const pct = h.precipitation_probability ?? 0;
    return `<div class="h-item ${isNow ? "now" : ""}">
      <span class="h-time">${isNow ? "Teraz" : hourLabel(h.datetime)}</span>
      <span class="h-icon">${condIcon(h.condition, h.weather_code)}</span>
      <span class="h-temp">${Math.round(+h.temperature)}°</span>
      <span class="h-rain">${pct > 0 ? pct + "%" : ""}</span>
    </div>`;
  }

  _day(d) {
    const pct = d.precipitation_probability ?? 0;
    return `<div class="d-row">
      <span class="d-name">${dayLabel(d.datetime)}</span>
      <span class="d-icon">${condIcon(d.condition, d.weather_code)}</span>
      <div class="d-bar-wrap">
        <span class="d-pct">${pct > 0 ? pct + "%" : ""}</span>
        <div class="bar"><div class="bar-f" style="width:${pct}%"></div></div>
      </div>
      <span class="d-lo">${Math.round(+(d.templow ?? 0))}°</span>
      <span class="d-hi">${Math.round(+(d.temperature ?? 0))}°</span>
    </div>`;
  }

  static getStubConfig() {
    return { entity: "weather.moja_pogoda" };
  }
}

customElements.define("open-meteo-weather-card", OpenMeteoWeatherCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "open-meteo-weather-card",
  name: "Open-Meteo Weather Card",
  description: "Nowoczesna karta pogodowa z prognozą godzinową i 7-dniową (Open-Meteo)",
  preview: true,
});

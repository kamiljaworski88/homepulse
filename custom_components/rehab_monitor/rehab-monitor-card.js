/**
 * Rehab Monitor Card — Custom Lovelace card for INTERMEDICUS slot monitoring.
 * Visual style mirrors HomePulse Card (same layout tokens and component patterns).
 *
 * Usage:
 *   type: custom:rehab-monitor-card
 *   title: "Rehab Monitor"   # optional
 */

// ── Styles (same design tokens as home-pulse-card) ───────────────────────────
const STYLES = `
  :host { display: block; }

  ha-card {
    padding: 16px;
    box-sizing: border-box;
  }

  /* ── Header ── */
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .header-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--primary-text-color);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .header-title ha-icon { color: var(--primary-color); }

  .btn-refresh {
    background: var(--primary-color);
    color: var(--text-primary-color);
    border: none;
    border-radius: 50%;
    width: 36px;
    height: 36px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: filter 0.2s;
    flex-shrink: 0;
  }

  .btn-refresh:hover { filter: brightness(1.15); }

  .btn-refresh.spinning ha-icon {
    display: block;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Slot list (mirrors .task-list) ── */
  .slot-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 10px; }

  .slot-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 12px;
    background: var(--card-background-color);
    border: 1px solid var(--divider-color);
    border-left: 3px solid var(--primary-color);
    transition: border-color 0.2s;
  }

  .slot-item.error {
    background: color-mix(in srgb, var(--error-color) 8%, var(--card-background-color));
    border-left-color: var(--error-color);
    border-color: var(--error-color);
  }

  /* mirrors .task-icon */
  .slot-icon {
    --mdc-icon-size: 28px;
    color: var(--primary-color);
    flex-shrink: 0;
  }

  .slot-item.error .slot-icon { color: var(--error-color); }

  /* mirrors .task-body */
  .slot-body { flex: 1; min-width: 0; }

  /* mirrors .task-title */
  .slot-title {
    font-weight: 500;
    font-size: 0.95rem;
    color: var(--primary-text-color);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* mirrors .task-meta */
  .slot-meta {
    font-size: 0.75rem;
    color: var(--secondary-text-color);
    margin-top: 2px;
  }

  /* mirrors .progress-bar — pulses to show "live" availability */
  .avail-bar {
    height: 5px;
    border-radius: 3px;
    background: var(--divider-color);
    margin-top: 6px;
    overflow: hidden;
  }

  .avail-fill {
    height: 100%;
    border-radius: 3px;
    width: 100%;
    background: var(--primary-color);
    animation: pulse 2.5s ease-in-out infinite;
  }

  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

  /* ── Empty state (mirrors HomePulse .empty-state) ── */
  .empty-state {
    text-align: center;
    padding: 24px 0;
    color: var(--secondary-text-color);
    font-size: 0.9rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }

  .empty-state ha-icon {
    --mdc-icon-size: 40px;
    display: block;
    color: var(--primary-color);
    opacity: 0.4;
    margin-bottom: 4px;
  }

  .empty-meta {
    font-size: 0.75rem;
    color: var(--disabled-text-color);
  }

  /* ── Timestamp ── */
  .timestamp {
    font-size: 0.72rem;
    color: var(--disabled-text-color);
    text-align: right;
    margin-bottom: 10px;
  }

  /* ── Divider ── */
  .divider {
    border: none;
    border-top: 1px solid var(--divider-color);
    margin: 10px 0;
  }

  /* ── Controls section ── */
  .controls { display: flex; flex-direction: column; gap: 4px; }

  .control-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 0;
  }

  .control-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.9rem;
    color: var(--primary-text-color);
  }

  .control-label ha-icon {
    --mdc-icon-size: 20px;
    color: var(--secondary-text-color);
  }

  /* Toggle pill (mirrors HA style) */
  .toggle {
    position: relative;
    width: 44px;
    height: 24px;
    border-radius: 12px;
    border: none;
    background: var(--divider-color);
    cursor: pointer;
    transition: background 0.2s;
    flex-shrink: 0;
    padding: 0;
  }

  .toggle.on { background: var(--primary-color); }

  .toggle-thumb {
    position: absolute;
    top: 3px;
    left: 3px;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #fff;
    transition: transform 0.2s;
    display: block;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
  }

  .toggle.on .toggle-thumb { transform: translateX(20px); }

  /* Location select (mirrors HomePulse form select) */
  .ctrl-select {
    background: var(--card-background-color);
    color: var(--primary-text-color);
    border: 1px solid var(--divider-color);
    border-radius: 8px;
    padding: 5px 8px;
    font-size: 0.85rem;
    outline: none;
    cursor: pointer;
    font-family: inherit;
    max-width: 150px;
    transition: border-color 0.2s;
  }

  .ctrl-select:focus { border-color: var(--primary-color); }

  /* ── Schedule section ── */
  .schedule-header {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.82rem;
    color: var(--secondary-text-color);
    cursor: pointer;
    user-select: none;
    padding: 4px 0;
  }

  .schedule-header ha-icon {
    --mdc-icon-size: 16px;
    color: var(--primary-color);
  }

  .sched-summary {
    margin-left: auto;
    font-size: 0.72rem;
    color: var(--disabled-text-color);
  }

  .sched-body {
    padding: 8px 0 4px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .sched-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }

  .sched-label {
    font-size: 0.82rem;
    color: var(--secondary-text-color);
  }

  /* mirrors HomePulse form input */
  .sched-input {
    background: var(--card-background-color);
    color: var(--primary-text-color);
    border: 1px solid var(--divider-color);
    border-radius: 8px;
    padding: 5px 8px;
    font-size: 0.85rem;
    outline: none;
    width: 72px;
    text-align: right;
    font-family: inherit;
    transition: border-color 0.2s;
  }

  .sched-input:focus { border-color: var(--primary-color); }
`;

// ── Web Component ─────────────────────────────────────────────────────────────
class RehabMonitorCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config  = {};
    this._hass    = null;
    this._spinning = false;
  }

  // ── HA interface ─────────────────────────────────────────────────────────

  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    const prev = this._hass;
    this._hass = hass;

    const watch = [
      "binary_sensor.rehab_dostepnosc",
      "sensor.rehab_wolne_terminy",
      "switch.rehab_monitor_active",
      "select.rehab_miejsce",
      "input_boolean.rehab_show_schedule",
      "number.rehab_scan_interval",
      "number.rehab_hour_start",
      "number.rehab_hour_end",
      "number.rehab_visit_hour_min",
    ];

    const changed = !prev || watch.some((id) => prev.states[id] !== hass.states[id]);
    if (changed) this._render();
  }

  static getStubConfig() {
    return { title: "Rehab Monitor" };
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  _s(id, fb = "") {
    return this._hass?.states[id]?.state ?? fb;
  }

  _a(id, attr, fb = null) {
    return this._hass?.states[id]?.attributes?.[attr] ?? fb;
  }

  _pad(n) {
    return String(Math.floor(Number(n))).padStart(2, "0");
  }

  _fmtDt(iso) {
    if (!iso) return null;
    try {
      return new Date(iso).toLocaleString("pl-PL", {
        day: "2-digit", month: "2-digit", year: "numeric",
        hour: "2-digit", minute: "2-digit",
      });
    } catch { return iso; }
  }

  _esc(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // ── Render ────────────────────────────────────────────────────────────────

  _render() {
    if (!this._hass) return;
    const root = this.shadowRoot;
    root.innerHTML = "";

    const style = document.createElement("style");
    style.textContent = STYLES;
    root.appendChild(style);

    const card = document.createElement("ha-card");
    card.innerHTML = this._html();
    root.appendChild(card);

    this._attachListeners(card);
  }

  _html() {
    const avail    = this._s("binary_sensor.rehab_dostepnosc") === "on";
    const terminy  = this._a("sensor.rehab_wolne_terminy", "terminy") ?? [];
    const blad     = this._a("sensor.rehab_wolne_terminy", "blad");
    const upd      = this._a("sensor.rehab_wolne_terminy", "ostatnia_aktualizacja");
    const monOn    = this._s("switch.rehab_monitor_active") === "on";
    const miejsce  = this._s("select.rehab_miejsce");
    const opts     = this._a("select.rehab_miejsce", "options") ?? [];
    const interval = this._s("number.rehab_scan_interval", "15");
    const hStart   = this._s("number.rehab_hour_start", "7");
    const hEnd     = this._s("number.rehab_hour_end", "23");
    const visitMin = this._s("number.rehab_visit_hour_min", "0");
    const showSch  = this._s("input_boolean.rehab_show_schedule") === "on";
    const title    = this._config.title ?? "Rehab Monitor";
    const updStr   = this._fmtDt(upd);

    const schedSummary = `co ${interval} min · ${this._pad(hStart)}:00–${this._pad(hEnd)}:00`;

    return `
      <div class="header">
        <div class="header-title">
          <ha-icon icon="mdi:hospital-building"></ha-icon>
          ${this._esc(title)}
        </div>
        <button class="btn-refresh${this._spinning ? " spinning" : ""}"
                data-action="refresh" title="Sprawdź teraz">
          <ha-icon icon="mdi:refresh"></ha-icon>
        </button>
      </div>

      <div class="slot-list">
        ${blad
          ? this._errorHtml(blad)
          : avail && terminy.length > 0
            ? terminy.map((t) => this._slotHtml(t)).join("")
            : this._emptyHtml(interval, hStart, hEnd)}
      </div>

      ${updStr ? `<div class="timestamp">Sprawdzono: ${updStr}</div>` : ""}

      <hr class="divider">

      <div class="controls">
        <div class="control-row">
          <div class="control-label">
            <ha-icon icon="mdi:hospital-box"></ha-icon>
            Monitorowanie
          </div>
          <button class="toggle${monOn ? " on" : ""}" data-action="toggle-mon"
                  title="${monOn ? "Wyłącz" : "Włącz"}">
            <span class="toggle-thumb"></span>
          </button>
        </div>

        <div class="control-row">
          <div class="control-label">
            <ha-icon icon="mdi:map-marker-outline"></ha-icon>
            Szukaj miejsca
          </div>
          <select class="ctrl-select" data-action="change-miejsce">
            ${opts.map((o) =>
              `<option value="${this._esc(o)}"${o === miejsce ? " selected" : ""}>${this._esc(o)}</option>`
            ).join("")}
          </select>
        </div>
      </div>

      <hr class="divider">

      <div class="schedule-header" data-action="toggle-schedule">
        <ha-icon icon="${showSch ? "mdi:chevron-up" : "mdi:chevron-down"}"></ha-icon>
        Harmonogram skanowania
        <span class="sched-summary">${schedSummary}</span>
      </div>

      ${showSch ? this._schedHtml(interval, hStart, hEnd, visitMin) : ""}
    `;
  }

  // ── HTML fragments ────────────────────────────────────────────────────────

  _slotHtml(t) {
    return `
      <div class="slot-item">
        <ha-icon class="slot-icon" icon="mdi:calendar-clock"></ha-icon>
        <div class="slot-body">
          <div class="slot-title">${this._esc(t.data)}&nbsp;&nbsp;${this._esc(t.godzina)}</div>
          <div class="slot-meta">👤 ${this._esc(t.rehabilitant)}&nbsp;&nbsp;·&nbsp;&nbsp;🏥 ${this._esc(t.miejsce)}</div>
          <div class="avail-bar"><div class="avail-fill"></div></div>
        </div>
      </div>`;
  }

  _errorHtml(blad) {
    return `
      <div class="slot-item error">
        <ha-icon class="slot-icon" icon="mdi:alert-circle-outline"></ha-icon>
        <div class="slot-body">
          <div class="slot-title">Błąd połączenia</div>
          <div class="slot-meta">${this._esc(blad)}</div>
        </div>
      </div>`;
  }

  _emptyHtml(interval, hStart, hEnd) {
    return `
      <div class="empty-state">
        <ha-icon icon="mdi:calendar-blank-outline"></ha-icon>
        Brak wolnych terminów
        <span class="empty-meta">co ${interval} min · ${this._pad(hStart)}:00–${this._pad(hEnd)}:00</span>
      </div>`;
  }

  _schedHtml(interval, hStart, hEnd, visitMin) {
    const row = (label, entity, value, min, max, step = 1) => `
      <div class="sched-row">
        <span class="sched-label">${label}</span>
        <input class="sched-input" type="number"
               min="${min}" max="${max}" step="${step}"
               value="${value}"
               data-entity="${entity}">
      </div>`;

    return `
      <div class="sched-body">
        ${row("Interwał (min)", "number.rehab_scan_interval", interval, 5, 120, 5)}
        ${row("Sprawdzaj od (godz.)", "number.rehab_hour_start", hStart, 0, 23)}
        ${row("Sprawdzaj do (godz.)", "number.rehab_hour_end", hEnd, 0, 23)}
        ${row("Pokaż wizyty od (godz.)", "number.rehab_visit_hour_min", visitMin, 0, 23)}
      </div>`;
  }

  // ── Event wiring ──────────────────────────────────────────────────────────

  _attachListeners(card) {
    card.addEventListener("click", (e) => {
      const el = e.target.closest("[data-action]");
      if (!el) return;
      switch (el.dataset.action) {
        case "refresh":
          this._hass.callService("button", "press", { entity_id: "button.rehab_sprawdz_teraz" });
          this._spinning = true;
          this._render();
          setTimeout(() => { this._spinning = false; this._render(); }, 1500);
          break;

        case "toggle-mon": {
          const on = this._s("switch.rehab_monitor_active") === "on";
          this._hass.callService("switch", on ? "turn_off" : "turn_on",
            { entity_id: "switch.rehab_monitor_active" });
          break;
        }

        case "toggle-schedule": {
          const on = this._s("input_boolean.rehab_show_schedule") === "on";
          this._hass.callService("input_boolean", on ? "turn_off" : "turn_on",
            { entity_id: "input_boolean.rehab_show_schedule" });
          break;
        }
      }
    });

    card.addEventListener("change", (e) => {
      const el = e.target;

      if (el.dataset.action === "change-miejsce") {
        this._hass.callService("select", "select_option", {
          entity_id: "select.rehab_miejsce",
          option: el.value,
        });
        return;
      }

      if (el.dataset.entity) {
        this._hass.callService("number", "set_value", {
          entity_id: el.dataset.entity,
          value: parseFloat(el.value),
        });
      }
    });
  }
}

customElements.define("rehab-monitor-card", RehabMonitorCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "rehab-monitor-card",
  name: "Rehab Monitor Card",
  description: "Monitoring wolnych terminów rehabilitacyjnych — INTERMEDICUS",
  preview: true,
});

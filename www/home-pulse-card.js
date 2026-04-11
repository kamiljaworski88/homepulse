/**
 * HomePulse Card — Custom Lovelace card for managing maintenance tasks.
 * Vanilla Web Component (no external dependencies).
 *
 * Usage in dashboard:
 *   type: custom:home-pulse-card
 *   title: "Konserwacja domu"   # optional
 */

const DOMAIN = "home_pulse";

// ── Icons by keyword ─────────────────────────────────────────────────────────
const ICON_MAP = [
  [/filtr|filter/i, "mdi:air-filter"],
  [/wod[ay]|water|kran/i, "mdi:water"],
  [/olej|oil/i, "mdi:oil"],
  [/czyszcz|clean|sprz[aą]t/i, "mdi:broom"],
  [/bateria|battery/i, "mdi:battery-medium"],
  [/opona|tire|kol[ao]/i, "mdi:tire"],
  [/ogród|garden|roślin/i, "mdi:flower"],
  [/komin|chimney/i, "mdi:fireplace"],
  [/inspek|przeglad|przegląd/i, "mdi:magnify"],
  [/szczo[tć]k|brush/i, "mdi:toothbrush"],
  [/kuch|kitchen/i, "mdi:chef-hat"],
  [/łazi|bath/i, "mdi:shower"],
];

function getIcon(title) {
  for (const [re, icon] of ICON_MAP) {
    if (re.test(title)) return icon;
  }
  return "mdi:wrench";
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function intervalLabel(value, unit) {
  const map = { days: "dni", weeks: "tyg.", months: "mies." };
  return `${value} ${map[unit] ?? unit}`;
}

function progressPercent(task) {
  const { interval_value, interval_unit, days_until_next } = task;
  let totalDays = interval_value;
  if (interval_unit === "weeks") totalDays *= 7;
  if (interval_unit === "months") totalDays *= 30;
  const elapsed = totalDays - days_until_next;
  return Math.min(100, Math.max(0, Math.round((elapsed / totalDays) * 100)));
}

// ── Styles ────────────────────────────────────────────────────────────────────
const STYLES = `
  :host { display: block; }

  ha-card {
    padding: 16px;
    box-sizing: border-box;
  }

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

  .btn-add {
    background: var(--primary-color);
    color: var(--text-primary-color);
    border: none;
    border-radius: 50%;
    width: 36px;
    height: 36px;
    font-size: 1.5rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: filter 0.2s, transform 0.15s;
    flex-shrink: 0;
  }

  .btn-add:hover { filter: brightness(1.15); }
  .btn-add.active { background: var(--error-color); transform: rotate(45deg); }

  /* ── Task list ── */
  .task-list { display: flex; flex-direction: column; gap: 10px; }

  .task-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 12px;
    background: var(--card-background-color, #ffffff);
    border: 1px solid var(--divider-color);
    transition: border-color 0.2s;
  }

  .task-item.overdue {
    background: color-mix(in srgb, var(--error-color) 8%, var(--card-background-color, #ffffff));
    border-left: 3px solid var(--error-color);
    border-color: var(--error-color);
  }

  .task-icon {
    --mdc-icon-size: 28px;
    color: var(--primary-color);
    flex-shrink: 0;
  }

  .task-icon.overdue { color: var(--error-color); }

  .task-body { flex: 1; min-width: 0; }

  .task-title {
    font-weight: 500;
    font-size: 0.95rem;
    color: var(--primary-text-color);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .task-meta {
    font-size: 0.75rem;
    color: var(--secondary-text-color);
    margin-top: 2px;
  }

  .task-meta.overdue { color: var(--error-color); font-weight: 600; }

  .progress-bar {
    height: 5px;
    border-radius: 3px;
    background: var(--divider-color);
    margin-top: 6px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.4s ease;
    background: var(--primary-color);
  }

  .progress-fill.warn   { background: var(--warning-color, #ff9800); }
  .progress-fill.danger { background: var(--error-color); }

  .task-actions { display: flex; gap: 4px; flex-shrink: 0; }

  .btn-icon {
    background: none;
    border: none;
    cursor: pointer;
    border-radius: 50%;
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s;
    color: var(--secondary-text-color);
  }

  .btn-icon:hover    { background: rgba(0,0,0,0.06); }
  .btn-icon.complete { color: var(--success-color, #4caf50); }
  .btn-icon.edit     { color: #ffffff; background: var(--primary-color); border-radius: 8px; }
  .btn-icon.delete   { color: var(--error-color); }
  .btn-icon.complete:hover { background: color-mix(in srgb, var(--success-color,#4caf50) 12%, transparent); }
  .btn-icon.edit:hover     { filter: brightness(1.12); }
  .btn-icon.delete:hover   { background: color-mix(in srgb, var(--error-color) 12%, transparent); }

  /* ── Forms (add & edit) ── */
  .add-form, .edit-form {
    border-radius: 12px;
    background: var(--card-background-color, #ffffff);
    border: 1px solid var(--primary-color);
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    animation: slideDown 0.18s ease;
  }

  .edit-form {
    border-color: var(--primary-color);
    width: 100%;
    box-sizing: border-box;
  }

  .edit-form-header {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--primary-color);
    margin-bottom: 2px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  @keyframes slideDown {
    from { opacity: 0; transform: translateY(-5px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .form-row { display: flex; gap: 8px; align-items: flex-end; }

  .form-label {
    font-size: 0.75rem;
    color: var(--secondary-text-color);
    margin-bottom: 3px;
  }

  .form-group { display: flex; flex-direction: column; flex: 1; }

  input, select {
    background: var(--card-background-color);
    color: var(--primary-text-color);
    border: 1px solid var(--divider-color);
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 0.9rem;
    outline: none;
    width: 100%;
    box-sizing: border-box;
    font-family: inherit;
    transition: border-color 0.2s;
  }

  input:focus, select:focus { border-color: var(--primary-color); }

  .form-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 4px; }

  .btn-submit {
    background: var(--primary-color);
    color: var(--text-primary-color);
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: filter 0.15s;
  }

  .btn-submit:hover { filter: brightness(1.1); }
  .btn-submit:disabled { opacity: 0.6; cursor: default; }

  .btn-cancel {
    background: none;
    border: 1px solid var(--divider-color);
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 0.9rem;
    cursor: pointer;
    color: var(--secondary-text-color);
    transition: background 0.15s;
  }

  .btn-cancel:hover { background: var(--divider-color); }

  .empty-state {
    text-align: center;
    padding: 24px 0;
    color: var(--secondary-text-color);
    font-size: 0.9rem;
  }

  .empty-state ha-icon {
    --mdc-icon-size: 40px;
    display: block;
    margin: 0 auto 8px;
    color: var(--primary-color);
    opacity: 0.5;
  }
`;

// ── Web Component ─────────────────────────────────────────────────────────────
class HomePulseCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._showForm = false;
    this._editingTaskId = null;
    this._form = { title: "", interval_value: "30", interval_unit: "days", google_calendar_entity: "" };
    this._editForm = { title: "", interval_value: "30", interval_unit: "days", google_calendar_entity: "" };
    this._submitting = false;
  }

  // ── HA interface ─────────────────────────────────────────────────────────

  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    const prevHass = this._hass;
    this._hass = hass;

    // Don't re-render while user is typing in add or edit form
    if (this._showForm || this._editingTaskId) return;

    // Re-render only when a home_pulse task entity actually changed
    const taskEntities = (states) =>
      Object.keys(states).filter((id) => states[id].attributes.task_id !== undefined);

    const prev = taskEntities(prevHass ? prevHass.states : {});
    const curr = taskEntities(hass.states);
    const changed =
      !prevHass ||
      prev.length !== curr.length ||
      curr.some((id) => prevHass.states[id] !== hass.states[id]);

    if (changed) this._render();
  }

  static getConfigElement() {
    return document.createElement("home-pulse-card-editor");
  }

  static getStubConfig() {
    return { title: "Konserwacja domu" };
  }

  // ── Data ─────────────────────────────────────────────────────────────────

  _getTasks() {
    if (!this._hass) return [];
    return Object.values(this._hass.states)
      .filter((s) => s.attributes.task_id !== undefined)
      .map((s) => ({
        entity_id: s.entity_id,
        task_id: s.attributes.task_id,
        title: s.attributes.title ?? s.attributes.friendly_name ?? s.entity_id,
        is_due: s.state === "on",
        days_until_next: s.attributes.days_until_next ?? 0,
        next_due_date: s.attributes.next_due_date ?? "",
        overdue_by_days: s.attributes.overdue_by_days ?? 0,
        interval_value: s.attributes.interval_value ?? 1,
        interval_unit: s.attributes.interval_unit ?? "days",
        last_performed: s.attributes.last_performed ?? "",
        google_calendar_entity: s.attributes.google_calendar_entity ?? "",
      }))
      .sort((a, b) => {
        if (a.is_due !== b.is_due) return a.is_due ? -1 : 1;
        return a.days_until_next - b.days_until_next;
      });
  }

  _getCalendars() {
    if (!this._hass) return [];
    return Object.keys(this._hass.states).filter((id) => id.startsWith("calendar."));
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  async _completeTask(taskId) {
    await this._hass.callService(DOMAIN, "complete_task", { task_id: taskId });
  }

  async _deleteTask(taskId) {
    await this._hass.callService(DOMAIN, "delete_task", { task_id: taskId });
  }

  _startEdit(task) {
    this._editingTaskId = task.task_id;
    this._editForm = {
      title: task.title,
      interval_value: String(task.interval_value),
      interval_unit: task.interval_unit,
      google_calendar_entity: task.google_calendar_entity,
    };
    this._showForm = false;
    this._render();
  }

  async _submitEdit() {
    const { title, interval_value, interval_unit, google_calendar_entity } = this._editForm;
    if (!title.trim()) return;
    this._submitting = true;
    this._render();
    try {
      await this._hass.callService(DOMAIN, "update_task", {
        task_id: this._editingTaskId,
        title: title.trim(),
        interval_value: parseInt(interval_value, 10),
        interval_unit,
        ...(google_calendar_entity ? { google_calendar_entity } : {}),
      });
      this._editingTaskId = null;
    } finally {
      this._submitting = false;
      this._render();
    }
  }

  async _submitForm() {
    const { title, interval_value, interval_unit, google_calendar_entity } = this._form;
    if (!title.trim()) return;
    this._submitting = true;
    this._render();
    try {
      await this._hass.callService(DOMAIN, "add_task", {
        title: title.trim(),
        interval_value: parseInt(interval_value, 10),
        interval_unit,
        ...(google_calendar_entity ? { google_calendar_entity } : {}),
      });
      this._form = { title: "", interval_value: "30", interval_unit: "days", google_calendar_entity: "" };
      this._showForm = false;
    } finally {
      this._submitting = false;
      this._render();
    }
  }

  // ── Rendering ─────────────────────────────────────────────────────────────

  _render() {
    const root = this.shadowRoot;
    root.innerHTML = "";

    const style = document.createElement("style");
    style.textContent = STYLES;
    root.appendChild(style);

    const card = document.createElement("ha-card");
    card.innerHTML = this._html();
    root.appendChild(card);

    this._attachEventListeners(card);
  }

  _html() {
    const tasks = this._getTasks();
    const title = this._config.title ?? "HomePulse";
    const calendars = this._getCalendars();

    return `
      <div class="header">
        <div class="header-title">
          <ha-icon icon="mdi:home-heart"></ha-icon>
          ${this._esc(title)}
        </div>
        <button class="btn-add${this._showForm ? " active" : ""}" data-action="toggle-form"
          title="${this._showForm ? "Anuluj" : "Dodaj zadanie"}">
          ${this._showForm ? "×" : "+"}
        </button>
      </div>

      <div class="task-list">
        ${this._showForm ? this._addFormHtml(calendars) : ""}
        ${tasks.length === 0 && !this._showForm ? this._emptyHtml() : ""}
        ${tasks.map((t) => this._editingTaskId === t.task_id
          ? this._editFormHtml(t, calendars)
          : this._taskHtml(t)
        ).join("")}
      </div>
    `;
  }

  _taskHtml(task) {
    const pct = progressPercent(task);
    const overdue = task.is_due && task.overdue_by_days > 0;
    const fillClass = overdue ? "danger" : pct >= 80 ? "warn" : "";

    let meta;
    if (overdue) {
      meta = `<span class="task-meta overdue">Zaległo ${task.overdue_by_days} dni temu</span>`;
    } else if (task.days_until_next === 0) {
      meta = `<span class="task-meta overdue">Termin dzisiaj!</span>`;
    } else {
      meta = `<span class="task-meta">Za ${task.days_until_next} dni · ${this._esc(task.next_due_date)} · co ${intervalLabel(task.interval_value, task.interval_unit)}</span>`;
    }

    return `
      <div class="task-item${overdue || task.days_until_next === 0 ? " overdue" : ""}">
        <ha-icon class="task-icon${overdue ? " overdue" : ""}" icon="${getIcon(task.title)}"></ha-icon>
        <div class="task-body">
          <div class="task-title">${this._esc(task.title)}</div>
          ${meta}
          <div class="progress-bar">
            <div class="progress-fill${fillClass ? " " + fillClass : ""}" style="width:${pct}%"></div>
          </div>
        </div>
        <div class="task-actions">
          <button class="btn-icon complete" data-action="complete" data-task-id="${task.task_id}" title="Oznacz jako wykonane">
            <ha-icon icon="mdi:check-circle-outline"></ha-icon>
          </button>
          <button class="btn-icon edit" data-action="edit" data-task-id="${task.task_id}" title="Edytuj zadanie">
            <ha-icon icon="mdi:pencil-outline"></ha-icon>
          </button>
          <button class="btn-icon delete" data-action="delete" data-task-id="${task.task_id}" title="Usuń zadanie">
            <ha-icon icon="mdi:trash-can-outline"></ha-icon>
          </button>
        </div>
      </div>
    `;
  }

  _editFormHtml(task, calendars) {
    const f = this._editForm;
    const calOptions = calendars
      .map((c) => `<option value="${c}"${f.google_calendar_entity === c ? " selected" : ""}>${c}</option>`)
      .join("");

    return `
      <div class="edit-form">
        <div class="edit-form-header">
          <ha-icon icon="mdi:pencil"></ha-icon>
          Edytuj zadanie
        </div>
        <div class="form-group">
          <div class="form-label">Nazwa zadania</div>
          <input type="text" data-field="edit-title" value="${this._esc(f.title)}" />
        </div>
        <div class="form-row">
          <div class="form-group" style="flex:0 0 80px">
            <div class="form-label">Co ile</div>
            <input type="number" data-field="edit-interval_value" min="1" max="365" value="${f.interval_value}" />
          </div>
          <div class="form-group" style="flex:0 0 110px">
            <div class="form-label">Jednostka</div>
            <select data-field="edit-interval_unit">
              <option value="days"${f.interval_unit === "days" ? " selected" : ""}>dni</option>
              <option value="weeks"${f.interval_unit === "weeks" ? " selected" : ""}>tygodnie</option>
              <option value="months"${f.interval_unit === "months" ? " selected" : ""}>miesiące</option>
            </select>
          </div>
          <div class="form-group">
            <div class="form-label">Kalendarz</div>
            <select data-field="edit-google_calendar_entity">
              <option value="">— brak —</option>
              ${calOptions}
            </select>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn-cancel" data-action="cancel-edit">Anuluj</button>
          <button class="btn-submit" data-action="save-edit" ${this._submitting ? "disabled" : ""}>
            ${this._submitting ? "Zapisywanie…" : "Zapisz"}
          </button>
        </div>
      </div>
    `;
  }

  _addFormHtml(calendars) {
    const f = this._form;
    const calOptions = calendars
      .map((c) => `<option value="${c}"${f.google_calendar_entity === c ? " selected" : ""}>${c}</option>`)
      .join("");

    return `
      <div class="add-form">
        <div class="form-group">
          <div class="form-label">Nazwa zadania</div>
          <input type="text" data-field="title" placeholder="np. Wymiana filtrów" value="${this._esc(f.title)}" />
        </div>
        <div class="form-row">
          <div class="form-group" style="flex:0 0 80px">
            <div class="form-label">Co ile</div>
            <input type="number" data-field="interval_value" min="1" max="365" value="${f.interval_value}" />
          </div>
          <div class="form-group" style="flex:0 0 110px">
            <div class="form-label">Jednostka</div>
            <select data-field="interval_unit">
              <option value="days"${f.interval_unit === "days" ? " selected" : ""}>dni</option>
              <option value="weeks"${f.interval_unit === "weeks" ? " selected" : ""}>tygodnie</option>
              <option value="months"${f.interval_unit === "months" ? " selected" : ""}>miesiące</option>
            </select>
          </div>
          <div class="form-group">
            <div class="form-label">Kalendarz (opcjonalnie)</div>
            <select data-field="google_calendar_entity">
              <option value="">— brak —</option>
              ${calOptions}
            </select>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn-cancel" data-action="cancel-form">Anuluj</button>
          <button class="btn-submit" data-action="submit-form" ${this._submitting ? "disabled" : ""}>
            ${this._submitting ? "Dodawanie…" : "Dodaj zadanie"}
          </button>
        </div>
      </div>
    `;
  }

  _emptyHtml() {
    return `
      <div class="empty-state">
        <ha-icon icon="mdi:playlist-check"></ha-icon>
        Brak zadań. Kliknij + aby dodać pierwsze zadanie.
      </div>
    `;
  }

  _esc(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ── Event wiring ──────────────────────────────────────────────────────────

  _attachEventListeners(card) {
    card.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-action]");
      if (!btn) return;
      const action = btn.dataset.action;
      const taskId = btn.dataset.taskId;

      switch (action) {
        case "toggle-form":
          this._showForm = !this._showForm;
          this._editingTaskId = null;
          this._render();
          break;
        case "cancel-form":
          this._showForm = false;
          this._render();
          break;
        case "submit-form":
          this._submitForm();
          break;
        case "complete":
          this._completeTask(taskId);
          break;
        case "edit": {
          const task = this._getTasks().find((t) => t.task_id === taskId);
          if (task) this._startEdit(task);
          break;
        }
        case "cancel-edit":
          this._editingTaskId = null;
          this._render();
          break;
        case "save-edit":
          this._submitEdit();
          break;
        case "delete":
          this._deleteTask(taskId);
          break;
      }
    });

    // Live-sync add form inputs
    card.addEventListener("input", (e) => {
      const el = e.target.closest("[data-field]");
      if (!el) return;
      const field = el.dataset.field;
      if (field.startsWith("edit-")) {
        this._editForm[field.slice(5)] = el.value;
      } else {
        this._form[field] = el.value;
      }
    });

    card.addEventListener("change", (e) => {
      const el = e.target.closest("[data-field]");
      if (!el) return;
      const field = el.dataset.field;
      if (field.startsWith("edit-")) {
        this._editForm[field.slice(5)] = el.value;
      } else {
        this._form[field] = el.value;
      }
    });
  }
}

customElements.define("home-pulse-card", HomePulseCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "home-pulse-card",
  name: "HomePulse Card",
  description: "Zarządzaj cyklicznymi zadaniami konserwacyjnymi z synchronizacją z Kalendarzem Google.",
  preview: true,
  documentationURL: "https://github.com/kamiljaworski88/homepulse",
});

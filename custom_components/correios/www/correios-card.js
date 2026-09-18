const CARD_TYPE = "correios-card";
const EDITOR_TYPE = "correios-card-editor";
const INTEGRATION_PLATFORM = "correios";
const PACKAGE_TRANSLATION_KEY = "package";
const UNAVAILABLE_STATES = ["unavailable", "unknown"];

const TRANSLATIONS = {
  en: {
    "card.title": "Correios",
    "card.in_transit": "in transit",
    "card.delivered": "delivered",
    "card.empty": "No packages being tracked.",
    "card.expected": "Expected",
    "card.delayed": "Delayed",
    "card.sent": "Sent by you",
    "card.to": "to",
    "card.details": "Details",
    "editor.title": "Title",
    "editor.show_delivered": "Show delivered packages",
    "editor.show_sent": "Show packages sent by you",
    "editor.show_history": "Allow expanding the tracking history",
    "editor.max_events": "Maximum events in the history",
  },
  "pt-BR": {
    "card.title": "Correios",
    "card.in_transit": "em trânsito",
    "card.delivered": "entregues",
    "card.empty": "Nenhum pacote sendo acompanhado.",
    "card.expected": "Previsão",
    "card.delayed": "Atrasado",
    "card.sent": "Enviado por você",
    "card.to": "para",
    "card.details": "Detalhes",
    "editor.title": "Título",
    "editor.show_delivered": "Mostrar pacotes entregues",
    "editor.show_sent": "Mostrar pacotes enviados por você",
    "editor.show_history": "Permitir expandir o histórico de rastreamento",
    "editor.max_events": "Máximo de eventos no histórico",
  },
};

const resolveLanguage = (hass) => {
  const language =
    (hass && (hass.locale?.language || hass.language || hass.selectedLanguage)) || "en";
  if (TRANSLATIONS[language]) return language;
  if (language.split("-")[0] === "pt") return "pt-BR";
  return "en";
};

const localize = (hass, key) =>
  TRANSLATIONS[resolveLanguage(hass)]?.[key] ?? TRANSLATIONS.en[key] ?? key;

const escapeHtml = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character],
  );

const REFERENCE_EVENING = new Date("January 1, 2023 22:00:00");
const dateFormatters = new Map();

const usesAmPm = (locale) => {
  const timeFormat = locale?.time_format ?? "language";
  if (timeFormat === "12") return true;
  if (timeFormat === "24") return false;
  const probeLanguage = timeFormat === "language" ? locale?.language : undefined;
  return REFERENCE_EVENING.toLocaleString(probeLanguage).includes("10");
};

const resolveTimeZone = (hass) =>
  hass.locale?.time_zone === "server" ? hass.config?.time_zone : undefined;

const dateFormatter = (language, options) => {
  const key = JSON.stringify([language, options]);
  if (!dateFormatters.has(key)) {
    dateFormatters.set(key, new Intl.DateTimeFormat(language, options));
  }
  return dateFormatters.get(key);
};

const localeSignature = (hass) => [
  hass.locale?.language,
  hass.locale?.time_format,
  hass.locale?.time_zone,
  hass.config?.time_zone,
];

const formatDateShort = (hass, isoDate) => {
  if (!isoDate) return "";
  const [year, month, day] = isoDate.split("-").map(Number);
  return dateFormatter(hass.locale?.language, {
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(year, month - 1, day)));
};

const formatShortDateTime = (hass, isoDateTime) => {
  if (!isoDateTime) return "";
  const amPm = usesAmPm(hass.locale);
  return dateFormatter(hass.locale?.language, {
    month: "short",
    day: "numeric",
    hour: amPm ? "numeric" : "2-digit",
    minute: "2-digit",
    hourCycle: amPm ? "h12" : "h23",
    timeZone: resolveTimeZone(hass),
  }).format(new Date(isoDateTime));
};

const packageIcon = (parcel) => {
  if (parcel.delivered) return "mdi:package-variant-closed-check";
  if (parcel.delayed) return "mdi:truck-alert";
  return "mdi:truck-delivery";
};

const packageTone = (parcel) => {
  if (parcel.delivered) return "delivered";
  if (parcel.delayed) return "delayed";
  return "transit";
};

class CorreiosCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._signature = null;
    this._expanded = new Set();
  }

  static getConfigElement() {
    return document.createElement(EDITOR_TYPE);
  }

  static getStubConfig() {
    return { type: `custom:${CARD_TYPE}` };
  }

  setConfig(config) {
    if (config.max_events != null && typeof config.max_events !== "number") {
      throw new Error(`${CARD_TYPE}: "max_events" must be a number`);
    }
    this._config = {
      title: null,
      show_delivered: true,
      show_sent: true,
      show_history: true,
      max_events: 10,
      ...config,
    };
    this._signature = null;
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 2 + this._packages().length;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6, min_rows: 2 };
  }

  _packages() {
    const hass = this._hass;
    if (!hass || !hass.entities) return [];
    return Object.values(hass.entities)
      .filter(
        (entry) =>
          entry.platform === INTEGRATION_PLATFORM &&
          entry.translation_key === PACKAGE_TRANSLATION_KEY &&
          !entry.hidden,
      )
      .map((entry) => ({ entry, state: hass.states[entry.entity_id] }))
      .filter(({ state }) => state && !UNAVAILABLE_STATES.includes(state.state))
      .map(({ entry, state }) => ({
        entityId: entry.entity_id,
        customName: entry.name || null,
        trackingCode: state.attributes.tracking_code ?? entry.entity_id,
        status: state.state,
        detail: state.attributes.detail,
        location: state.attributes.location,
        category: state.attributes.category,
        expectedDelivery: state.attributes.expected_delivery,
        lastEventAt: state.attributes.last_event_at,
        delivered: state.attributes.delivered === true,
        delayed: state.attributes.delayed === true,
        sent: state.attributes.direction === "sent",
        events: Array.isArray(state.attributes.events) ? state.attributes.events : [],
      }))
      .filter((parcel) => this._config.show_delivered || !parcel.delivered)
      .filter((parcel) => this._config.show_sent || !parcel.sent)
      .sort(
        (left, right) =>
          Number(left.delivered) - Number(right.delivered) ||
          String(right.lastEventAt ?? "").localeCompare(String(left.lastEventAt ?? "")),
      );
  }

  _render() {
    if (!this._hass) return;
    const packages = this._packages();
    const language = resolveLanguage(this._hass);
    const signature = JSON.stringify([
      this._config,
      language,
      localeSignature(this._hass),
      [...this._expanded],
      packages.map((parcel) => [
        parcel.entityId,
        parcel.customName,
        parcel.status,
        parcel.lastEventAt,
        parcel.expectedDelivery,
        parcel.delivered,
        parcel.delayed,
        parcel.events.length,
      ]),
    ]);
    if (signature === this._signature) return;
    this._signature = signature;

    const inTransit = packages.filter((parcel) => !parcel.delivered).length;
    const delivered = packages.length - inTransit;
    const summary = [`${inTransit} ${localize(this._hass, "card.in_transit")}`];
    if (this._config.show_delivered && delivered > 0) {
      summary.push(`${delivered} ${localize(this._hass, "card.delivered")}`);
    }

    this.shadowRoot.innerHTML = `
      <style>${CorreiosCard.styles}</style>
      <ha-card>
        <div class="header">
          <ha-icon icon="mdi:package-variant"></ha-icon>
          <div class="heading">
            <div class="title">${escapeHtml(this._config.title ?? localize(this._hass, "card.title"))}</div>
            <div class="summary">${escapeHtml(summary.join(" · "))}</div>
          </div>
        </div>
        ${
          packages.length === 0
            ? `<div class="empty">${escapeHtml(localize(this._hass, "card.empty"))}</div>`
            : `<div class="packages">${packages.map((parcel) => this._renderPackage(parcel)).join("")}</div>`
        }
      </ha-card>`;

    this.shadowRoot.querySelectorAll(".package-summary").forEach((element) =>
      element.addEventListener("click", () => this._toggle(element.dataset.id)),
    );
    this.shadowRoot.querySelectorAll(".details").forEach((element) =>
      element.addEventListener("click", (event) => {
        event.stopPropagation();
        this.dispatchEvent(
          new CustomEvent("hass-more-info", {
            detail: { entityId: element.dataset.id },
            bubbles: true,
            composed: true,
          }),
        );
      }),
    );
  }

  _toggle(entityId) {
    if (!this._config.show_history) {
      this.dispatchEvent(
        new CustomEvent("hass-more-info", {
          detail: { entityId },
          bubbles: true,
          composed: true,
        }),
      );
      return;
    }
    if (this._expanded.has(entityId)) this._expanded.delete(entityId);
    else this._expanded.add(entityId);
    this._render();
  }

  _renderPackage(parcel) {
    const hass = this._hass;
    const expanded = this._config.show_history && this._expanded.has(parcel.entityId);
    const name = parcel.customName ?? parcel.trackingCode;
    const badges = [];
    if (parcel.delayed && !parcel.delivered) {
      badges.push(`<span class="badge delayed">${escapeHtml(localize(hass, "card.delayed"))}</span>`);
    }
    if (parcel.sent) {
      badges.push(`<span class="badge">${escapeHtml(localize(hass, "card.sent"))}</span>`);
    }
    const facts = [parcel.location, formatShortDateTime(hass, parcel.lastEventAt)].filter(Boolean);
    if (parcel.customName) facts.unshift(parcel.trackingCode);

    return `
      <div class="package ${packageTone(parcel)}">
        <div class="package-summary" data-id="${escapeHtml(parcel.entityId)}">
          <div class="bubble"><ha-icon icon="${packageIcon(parcel)}"></ha-icon></div>
          <div class="body">
            <div class="row">
              <span class="name" title="${escapeHtml(name)}">${escapeHtml(name)}</span>
              ${badges.join("")}
            </div>
            <div class="status" title="${escapeHtml(parcel.status)}">${escapeHtml(parcel.status)}</div>
            <div class="facts" title="${escapeHtml(facts.join(" · "))}">${escapeHtml(facts.join(" · "))}</div>
          </div>
          ${
            parcel.expectedDelivery && !parcel.delivered
              ? `<div class="expected">
                  <span class="expected-label">${escapeHtml(localize(hass, "card.expected"))}</span>
                  <span class="expected-date">${escapeHtml(formatDateShort(hass, parcel.expectedDelivery))}</span>
                </div>`
              : ""
          }
          ${
            this._config.show_history
              ? `<ha-icon class="chevron" icon="${expanded ? "mdi:chevron-up" : "mdi:chevron-down"}"></ha-icon>`
              : ""
          }
        </div>
        ${expanded ? this._renderHistory(parcel) : ""}
      </div>`;
  }

  _renderHistory(parcel) {
    const hass = this._hass;
    const events = parcel.events.slice(0, this._config.max_events);
    return `
      <div class="history">
        ${parcel.category ? `<div class="category">${escapeHtml(parcel.category)}</div>` : ""}
        <ol class="timeline">
          ${events
            .map((event) => {
              const route = [
                event.location,
                event.destination ? `${localize(hass, "card.to")} ${event.destination}` : null,
              ]
                .filter(Boolean)
                .join(" ");
              return `
                <li>
                  <div class="event-description">${escapeHtml(event.description ?? "")}</div>
                  ${event.detail ? `<div class="event-detail">${escapeHtml(event.detail)}</div>` : ""}
                  <div class="event-facts">${escapeHtml(
                    [formatShortDateTime(hass, event.occurred_at), route].filter(Boolean).join(" · "),
                  )}</div>
                </li>`;
            })
            .join("")}
        </ol>
        <button class="details" data-id="${escapeHtml(parcel.entityId)}">
          ${escapeHtml(localize(hass, "card.details"))}
        </button>
      </div>`;
  }

  static get styles() {
    return `
      ha-card { padding: 16px; }
      .header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
      .header > ha-icon { color: var(--primary-color); }
      .title { font-size: 1.2em; font-weight: 500; color: var(--primary-text-color); }
      .summary, .facts, .event-facts, .category, .expected-label {
        font-size: 0.85em; color: var(--secondary-text-color);
      }
      .empty { padding: 16px 0 8px; color: var(--secondary-text-color); text-align: center; }
      .packages { display: flex; flex-direction: column; }
      .package + .package { border-top: 1px solid var(--divider-color); }
      .package-summary {
        display: flex; align-items: center; gap: 12px; padding: 12px 0; cursor: pointer;
      }
      .bubble {
        flex: none; display: flex; align-items: center; justify-content: center;
        width: 40px; height: 40px; border-radius: 50%;
        color: var(--tone); background: color-mix(in srgb, var(--tone) 18%, transparent);
      }
      .transit { --tone: var(--primary-color); }
      .delivered { --tone: var(--success-color); }
      .delayed { --tone: var(--warning-color); }
      .body { flex: 1; min-width: 0; }
      .row { display: flex; align-items: center; gap: 8px; min-width: 0; }
      .name { font-weight: 500; color: var(--primary-text-color); letter-spacing: 0.02em; }
      .name, .status, .facts { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .status { color: var(--primary-text-color); font-size: 0.95em; }
      .badge {
        flex: none; font-size: 0.7em; padding: 1px 8px; border-radius: 10px;
        color: var(--secondary-text-color); border: 1px solid var(--divider-color);
      }
      .badge.delayed { color: var(--warning-color); border-color: var(--warning-color); }
      .expected { flex: none; display: flex; flex-direction: column; align-items: flex-end; }
      .expected-date { font-weight: 500; color: var(--primary-text-color); white-space: nowrap; }
      .chevron { flex: none; color: var(--secondary-text-color); }
      .history { padding: 0 0 12px 52px; }
      .category { margin-bottom: 8px; }
      .timeline { list-style: none; margin: 0; padding: 0; }
      .timeline li { position: relative; padding: 0 0 12px 22px; }
      .timeline li:last-child { padding-bottom: 4px; }
      .timeline li::before {
        content: ""; position: absolute; z-index: 1; box-sizing: border-box;
        left: 0; top: 5px; width: 10px; height: 10px; border-radius: 50%;
        background: var(--divider-color);
        box-shadow: 0 0 0 3px var(--ha-card-background, var(--card-background-color, transparent));
      }
      .timeline li::after {
        content: ""; position: absolute; left: 4px; top: 10px; bottom: -10px;
        width: 2px; background: var(--divider-color);
      }
      .timeline li:last-child::after { display: none; }
      .timeline li:first-child::before { background: var(--tone); }
      .event-description { color: var(--primary-text-color); font-size: 0.95em; line-height: 20px; }
      .event-detail { color: var(--secondary-text-color); font-size: 0.85em; overflow-wrap: anywhere; }
      .details {
        margin-top: 4px; padding: 4px 0; border: none; background: none; cursor: pointer;
        font: inherit; font-size: 0.85em; font-weight: 500; color: var(--primary-color);
      }
    `;
  }
}

class CorreiosCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _schema() {
    return [
      { name: "title", selector: { text: {} } },
      { name: "show_delivered", selector: { boolean: {} } },
      { name: "show_sent", selector: { boolean: {} } },
      { name: "show_history", selector: { boolean: {} } },
      { name: "max_events", selector: { number: { min: 1, max: 50, mode: "box" } } },
    ];
  }

  _render() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (field) => localize(this._hass, `editor.${field.name}`);
      this._form.addEventListener("value-changed", (event) => {
        const config = { ...this._config, ...event.detail.value };
        for (const [key, value] of Object.entries(config)) {
          if (value === "" || value == null) delete config[key];
        }
        config.type = this._config.type ?? `custom:${CARD_TYPE}`;
        this.dispatchEvent(
          new CustomEvent("config-changed", {
            detail: { config },
            bubbles: true,
            composed: true,
          }),
        );
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.schema = this._schema();
    this._form.data = {
      title: this._config.title ?? "",
      show_delivered: this._config.show_delivered ?? true,
      show_sent: this._config.show_sent ?? true,
      show_history: this._config.show_history ?? true,
      max_events: this._config.max_events ?? 10,
    };
  }
}

if (!customElements.get(CARD_TYPE)) {
  customElements.define(CARD_TYPE, CorreiosCard);
}
if (!customElements.get(EDITOR_TYPE)) {
  customElements.define(EDITOR_TYPE, CorreiosCardEditor);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === CARD_TYPE)) {
  window.customCards.push({
    type: CARD_TYPE,
    name: "Correios",
    description: "Packages tracked by the Correios integration, with their tracking history.",
    preview: true,
    documentationURL: "https://github.com/roquerodrigo/ha-correios",
  });
}

console.info("%c CORREIOS-CARD %c loaded ", "color:#fff;background:#00416b", "");

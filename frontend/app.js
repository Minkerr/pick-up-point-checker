const API_BASE = "http://127.0.0.1:8000";

const form          = document.getElementById("check-form");
const submitBtn     = document.getElementById("submit-btn");
const addressInput  = document.getElementById("address-input");
const errorBanner   = document.getElementById("error-banner");
const resultsDiv    = document.getElementById("results");
const coordsDisplay = document.getElementById("coords-display");
const ozonBody      = document.getElementById("ozon-body");
const wbBody        = document.getElementById("wb-body");
const ymBody        = document.getElementById("ym-body");
const ozonLink      = document.getElementById("ozon-link");
const wbLink        = document.getElementById("wb-link");
const ymLink        = document.getElementById("ym-link");

// ── Leaflet map ────────────────────────────────────────
const map = L.map("map", { attributionControl: false }).setView([55.751, 37.618], 10);
L.control.attribution({ prefix: false }).addTo(map);

L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
  attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, © <a href="https://carto.com/">CARTO</a>',
  maxZoom: 19,
}).addTo(map);

const pinIcon = L.divIcon({
  html: `<svg width="28" height="36" viewBox="0 0 28 36" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M14 0C6.268 0 0 6.268 0 14c0 9.333 14 22 14 22S28 23.333 28 14C28 6.268 21.732 0 14 0z" fill="#4f6ef7"/>
    <circle cx="14" cy="14" r="6" fill="white"/>
  </svg>`,
  className: "",
  iconSize: [28, 36],
  iconAnchor: [14, 36],
});

let marker = null;

function placeMarker(lat, lon) {
  if (marker) marker.setLatLng([lat, lon]);
  else marker = L.marker([lat, lon], { icon: pinIcon }).addTo(map);
}

map.on("click", (e) => {
  const { lat, lng } = e.latlng;
  placeMarker(lat, lng);
  checkByCoords(lat, lng);
});

// ── Form submit ────────────────────────────────────────
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const address = addressInput.value.trim();
  if (!address) return;

  setLoading(true);
  hideError();
  hideResults();

  try {
    const resp = await fetch(`${API_BASE}/api/check-location?` + new URLSearchParams({ address }));
    const data = await resp.json();
    if (!resp.ok) { showError(data.detail || "Неизвестная ошибка"); return; }

    renderResults(data);
    placeMarker(data.coordinates.lat, data.coordinates.lon);
    map.flyTo([data.coordinates.lat, data.coordinates.lon], 15, { duration: 0.8 });
  } catch {
    showError("Не удалось подключиться к серверу.");
  } finally {
    setLoading(false);
  }
});

// ── Map click ──────────────────────────────────────────
async function checkByCoords(lat, lon) {
  setLoading(true);
  hideError();
  hideResults();
  addressInput.value = "";

  try {
    const resp = await fetch(`${API_BASE}/api/check-location?` + new URLSearchParams({ lat, lon }));
    const data = await resp.json();
    if (!resp.ok) { showError(data.detail || "Неизвестная ошибка"); return; }
    renderResults(data);
  } catch {
    showError("Не удалось подключиться к серверу.");
  } finally {
    setLoading(false);
  }
}

// ── Render ─────────────────────────────────────────────
function renderResults(data) {
  const { lat, lon } = data.coordinates;
  coordsDisplay.textContent = `${lat.toFixed(5)}, ${lon.toFixed(5)}`;

  ozonLink.href = `https://pvz-map.ozon.ru/?z=16&lat=${lat}&lon=${lon}&open=1`;
  wbLink.href   = `https://map.wb.ru/?lat=${lat}&lng=${lon}&tab=discovery&area=70&turnover=6000000&rent=50000&salary=70000&other=10000#14.01/${lat}/${lon}`;
  ymLink.href   = "https://logistics.market.yandex.ru/tpl-partner/brand-map";

  ozonBody.innerHTML = buildCardHTML(data.ozon,          ozonTooltips);
  wbBody.innerHTML   = buildCardHTML(data.wb,            wbTooltips);
  ymBody.innerHTML   = buildCardHTML(data.yandex_market, ymTooltips);

  resultsDiv.classList.remove("hidden");
}

// ── Tooltips for top-level card fields ─────────────────
const ozonTooltips = {
  status:  "Разрешает ли Ozon открытие ПВЗ в данной точке",
  tariff:  "Процент от оборота ПВЗ, который Ozon выплачивает партнёру",
  support: "Суммарная финансовая поддержка по программе MB (MaxBrand)",
};
const wbTooltips = {
  status:  "Разрешает ли WB открытие ПВЗ в данной точке",
  tariff:  "Итоговый процент вознаграждения (базовый + бонус)",
  support: "Полное ежемесячное вознаграждение партнёра от WB",
};
const ymTooltips = {
  status:  "Наличие субсидии от Яндекс.Маркета для данной зоны",
  tariff:  null,
  support: "Ежемесячная субсидия от Яндекс.Маркета",
};

function buildCardHTML(result, tips) {
  const statusLabels = {
    approved: "Открытие возможно",
    denied:   "Открытие невозможно",
    limited:  "Ограниченно",
    error:    "Ошибка запроса",
  };

  const statusLine = `
    <div class="stat">
      ${labelWithTip("Статус", tips.status)}
      <span class="badge badge-${result.status}">${statusLabels[result.status] ?? result.status}</span>
    </div>`;

  const tariffLine = result.tariff != null
    ? `<div class="stat">${labelWithTip("Тариф", tips.tariff)}<span class="stat-value">${result.tariff}%</span></div>`
    : "";

  let supportLine = "";
  if (result.financial_support != null) {
    supportLine = `
      <div class="stat">
        ${labelWithTip("Поддержка", tips.support)}
        <div>
          <div class="stat-value">${formatMoney(result.financial_support)}</div>
          ${result.financial_support_label
            ? `<div class="stat-sublabel">${result.financial_support_label}</div>`
            : ""}
        </div>
      </div>`;
  }

  const extraLines = (result.extra_fields || []).map(f => `
    <div class="stat">
      ${labelWithTip(f.label, f.tooltip)}
      <span class="stat-value stat-extra">${f.value}</span>
    </div>`).join("");

  const errorLine = result.status === "error"
    ? `<div style="font-size:0.78rem;color:#c0392b;word-break:break-word">${result.raw?.error ?? ""}</div>`
    : "";

  return statusLine + tariffLine + supportLine + extraLines + errorLine;
}

function labelWithTip(text, tooltip) {
  if (!tooltip) return `<span class="stat-label">${text}</span>`;
  return `
    <span class="info-wrap stat-label">
      ${text}
      <span class="info-btn">i
        <span class="info-tip">${tooltip}</span>
      </span>
    </span>`;
}

function formatMoney(n) {
  return new Intl.NumberFormat("ru-RU", {
    style: "currency", currency: "RUB", maximumFractionDigits: 0,
  }).format(n);
}

function setLoading(on) {
  submitBtn.disabled = on;
  submitBtn.textContent = on ? "…" : "Найти";
}
function showError(msg) { errorBanner.textContent = msg; errorBanner.classList.remove("hidden"); }
function hideError()    { errorBanner.classList.add("hidden"); }
function hideResults()  { resultsDiv.classList.add("hidden"); }

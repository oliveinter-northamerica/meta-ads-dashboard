const fmtKRW = new Intl.NumberFormat('en-US', {
  style: 'currency', currency: meta.currency, maximumFractionDigits: 0,
});
const fmtUSD = new Intl.NumberFormat('en-US', {
  style: 'currency', currency: amazonMeta.currency, maximumFractionDigits: 0,
});
const fmtKRWCompact = new Intl.NumberFormat('en-US', {
  style: 'currency', currency: meta.currency, notation: 'compact', maximumFractionDigits: 1,
});
const fmtUSDCompact = new Intl.NumberFormat('en-US', {
  style: 'currency', currency: amazonMeta.currency, notation: 'compact', maximumFractionDigits: 1,
});
const fmtNum = (v) => v.toLocaleString('en-US');

function renderHeader() {
  document.getElementById('page-title').textContent = `${meta.accountName} · Meta × ${amazonMeta.marketplace}`;
  document.getElementById('page-subtitle').textContent =
    `Meta ${meta.dateRange.split('(')[0].trim()} · Amazon ${amazonMeta.rangeStart} → ${amazonMeta.rangeEnd}`
    + ` · FX ₩${amazonMeta.usdKrw.toLocaleString()}/USD`;
  document.getElementById('amazon-marketplace-title').textContent =
    `Amazon — ${amazonMeta.marketplace}`;
}

function renderFreshness() {
  const todayStr = meta.generatedAt;
  const lastAmazon = amazonMeta.dataAvailableThrough;
  const banner = document.getElementById('freshness-banner');
  if (lastAmazon < todayStr) {
    banner.classList.remove('hidden');
    banner.innerHTML =
      `<strong>Amazon data freshness:</strong> latest day available is <code>${lastAmazon}</code>, ` +
      `but Meta data is current through <code>2026-06-03</code>. ` +
      `KPIs and the joint table use the overlap window only. The dual-axis chart shows each side over its own available range.`;
  }
}

function renderKpis() {
  const totalMetaSpendKrw = amazonDaily.reduce((s, r) => s + r.metaSpendKrw, 0);
  const totalAmazonSalesUsd = amazonDaily.reduce((s, r) => s + r.amazonSales, 0);
  const totalAmazonSalesKrw = amazonDaily.reduce((s, r) => s + r.amazonSalesKrw, 0);
  const totalAmazonOrders = amazonDaily.reduce((s, r) => s + r.amazonOrders, 0);
  const roas = totalMetaSpendKrw ? totalAmazonSalesKrw / totalMetaSpendKrw : 0;

  const cards = [
    { label: `Meta spend · ${amazonDaily.length}d overlap`, value: fmtKRW.format(totalMetaSpendKrw), sub: 'Account-level total' },
    { label: 'Amazon sales',  value: fmtUSD.format(totalAmazonSalesUsd), sub: `${fmtKRW.format(totalAmazonSalesKrw)} @ ₩${amazonMeta.usdKrw}/USD` },
    { label: 'Amazon orders', value: fmtNum(totalAmazonOrders), sub: 'Sum across overlap window' },
    { label: 'Joint ROAS',    value: roas ? roas.toFixed(2) + '×' : '—', sub: 'Amazon sales (KRW) ÷ Meta spend (KRW)' },
  ];

  document.getElementById('kpi-cards').innerHTML = cards.map(c => `
    <div class="bg-white border border-slate-200 rounded-xl p-5">
      <p class="text-xs font-medium uppercase tracking-wide text-slate-500">${c.label}</p>
      <p class="text-2xl font-semibold mt-2">${c.value}</p>
      <p class="text-xs text-slate-500 mt-1">${c.sub}</p>
    </div>
  `).join('');
}

function renderCombinedChart() {
  // Build a union of dates so each axis can render its own range without forcing them to overlap.
  const dates = new Set();
  amazonDaily.forEach(r => dates.add(r.date));
  // Add the last 30 Meta days that span the Amazon window plus current period.
  timeseries.slice(-30).forEach(r => dates.add(r.date));
  const sortedDates = [...dates].sort();

  const metaByDate = Object.fromEntries(timeseries.map(r => [r.date, r.spend]));
  const amazonByDate = Object.fromEntries(amazonDaily.map(r => [r.date, r.amazonSales]));

  const metaSeries = sortedDates.map(d => metaByDate[d] ?? null);
  const amazonSeries = sortedDates.map(d => amazonByDate[d] ?? null);

  new Chart(document.getElementById('combined-chart'), {
    type: 'line',
    data: {
      labels: sortedDates.map(d => d.slice(5)),
      datasets: [
        {
          label: 'Meta spend (KRW)',
          data: metaSeries,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.08)',
          fill: true,
          tension: 0.35,
          yAxisID: 'yMeta',
          pointRadius: 0,
          borderWidth: 2,
          spanGaps: true,
        },
        {
          label: 'Amazon sales (USD)',
          data: amazonSeries,
          borderColor: '#f97316',
          backgroundColor: 'transparent',
          tension: 0.35,
          yAxisID: 'yAmazon',
          pointRadius: 2,
          borderWidth: 2,
          spanGaps: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { display: false } },
      scales: {
        yMeta:   { position: 'left',  ticks: { callback: v => fmtKRWCompact.format(v) }, grid: { color: '#f1f5f9' } },
        yAmazon: { position: 'right', ticks: { callback: v => fmtUSDCompact.format(v) }, grid: { display: false } },
        x:       { grid: { display: false } },
      },
    },
  });
}

function renderSummaries() {
  // Meta summary uses the full 30d window from data.js.
  const last30 = timeseries.slice(-30);
  const metaSpend = last30.reduce((s, r) => s + r.spend, 0);
  const metaImp = last30.reduce((s, r) => s + r.impressions, 0);
  const metaClicks = last30.reduce((s, r) => s + r.clicks, 0);
  const metaCtr = metaImp ? (metaClicks / metaImp) * 100 : 0;
  const metaCpc = metaClicks ? metaSpend / metaClicks : 0;

  document.getElementById('meta-period').textContent = meta.dateRange;
  document.getElementById('meta-summary').innerHTML = [
    ['Spend',       fmtKRW.format(metaSpend)],
    ['Impressions', fmtNum(metaImp)],
    ['Clicks',      fmtNum(metaClicks)],
    ['CTR',         metaCtr.toFixed(2) + '%'],
    ['CPC',         fmtKRW.format(Math.round(metaCpc))],
  ].map(([k, v]) =>
    `<div class="flex justify-between"><span class="text-slate-500">${k}</span><span class="font-medium tabular-nums">${v}</span></div>`
  ).join('');

  // Amazon summary uses only available days.
  const amaSales = amazonDaily.reduce((s, r) => s + r.amazonSales, 0);
  const amaOrders = amazonDaily.reduce((s, r) => s + r.amazonOrders, 0);
  const amaUnits = amazonDaily.reduce((s, r) => s + r.amazonUnits, 0);
  const aov = amaOrders ? amaSales / amaOrders : 0;
  const upo = amaOrders ? amaUnits / amaOrders : 0;

  document.getElementById('amazon-period').textContent =
    `${amazonMeta.rangeStart} → ${amazonMeta.rangeEnd} (${amazonDaily.length} days)`;
  document.getElementById('amazon-summary').innerHTML = [
    ['Total sales', fmtUSD.format(amaSales)],
    ['Orders',      fmtNum(amaOrders)],
    ['Units',       fmtNum(amaUnits)],
    ['AOV',         fmtUSD.format(aov)],
    ['Units/order', upo.toFixed(2)],
  ].map(([k, v]) =>
    `<div class="flex justify-between"><span class="text-slate-500">${k}</span><span class="font-medium tabular-nums">${v}</span></div>`
  ).join('');
}

function renderJointTable() {
  const tbody = document.getElementById('joint-tbody');
  tbody.innerHTML = amazonDaily.map(r => `
    <tr class="hover:bg-slate-50">
      <td class="px-6 py-3 font-medium">${r.date}</td>
      <td class="px-4 py-3 text-right tabular-nums">${fmtKRW.format(r.metaSpendKrw)}</td>
      <td class="px-4 py-3 text-right tabular-nums">${fmtUSD.format(r.amazonSales)}</td>
      <td class="px-4 py-3 text-right tabular-nums">${fmtNum(r.amazonOrders)}</td>
      <td class="px-4 py-3 text-right tabular-nums">${fmtNum(r.amazonUnits)}</td>
      <td class="px-6 py-3 text-right tabular-nums font-medium">${r.roasKrw ? r.roasKrw.toFixed(2) + '×' : '—'}</td>
    </tr>
  `).join('');
}

const steps = [
  ['header',     renderHeader],
  ['freshness',  renderFreshness],
  ['kpis',       renderKpis],
  ['combined',   renderCombinedChart],
  ['summaries',  renderSummaries],
  ['joint',      renderJointTable],
];
for (const [name, fn] of steps) {
  try { fn(); } catch (e) { console.error(`meta-amazon: ${name} failed`, e); }
}

(function () {
  const { buildDailySeries, CAMPAIGNS, TOP_ADS, PLACEMENTS, AGE_BUCKETS, AGE_GENDER } = window.MOCK;

  const state = {
    range: 30,
    objective: "all",
    series: [],
    campaigns: CAMPAIGNS.slice(),
    sortKey: "spend",
    sortDir: "desc",
    search: "",
  };

  const fmt = {
    money: (n) => "$" + Math.round(n).toLocaleString(),
    int: (n) => Math.round(n).toLocaleString(),
    pct: (n) => n.toFixed(2) + "%",
    multi: (n) => n.toFixed(2) + "x",
  };

  // Chart defaults
  Chart.defaults.color = "#8b91a3";
  Chart.defaults.borderColor = "#232836";
  Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Roboto, Arial, sans-serif";

  const charts = {};

  function totals(series) {
    return series.reduce(
      (a, d) => ({
        spend: a.spend + d.spend,
        revenue: a.revenue + d.revenue,
        impressions: a.impressions + d.impressions,
        clicks: a.clicks + d.clicks,
        conversions: a.conversions + d.conversions,
      }),
      { spend: 0, revenue: 0, impressions: 0, clicks: 0, conversions: 0 }
    );
  }

  function deltaPct(curr, prev) {
    if (!prev) return 0;
    return ((curr - prev) / prev) * 100;
  }

  function renderKPIs() {
    const fullSeries = buildDailySeries(state.range * 2);
    const prev = fullSeries.slice(0, state.range);
    const curr = state.series;
    const tCurr = totals(curr);
    const tPrev = totals(prev);

    const ctr = (tCurr.clicks / tCurr.impressions) * 100;
    const cpc = tCurr.spend / tCurr.clicks;
    const roas = tCurr.revenue / tCurr.spend;
    const cpa = tCurr.spend / tCurr.conversions;
    const cpm = (tCurr.spend / tCurr.impressions) * 1000;

    const ctrPrev = (tPrev.clicks / tPrev.impressions) * 100;
    const cpcPrev = tPrev.spend / tPrev.clicks;
    const roasPrev = tPrev.revenue / tPrev.spend;
    const cpaPrev = tPrev.spend / tPrev.conversions;

    const kpis = [
      { label: "Spend",       value: fmt.money(tCurr.spend),     delta: deltaPct(tCurr.spend, tPrev.spend),     better: "lower" },
      { label: "Revenue",     value: fmt.money(tCurr.revenue),   delta: deltaPct(tCurr.revenue, tPrev.revenue), better: "higher" },
      { label: "ROAS",        value: fmt.multi(roas),            delta: deltaPct(roas, roasPrev),               better: "higher" },
      { label: "Conversions", value: fmt.int(tCurr.conversions), delta: deltaPct(tCurr.conversions, tPrev.conversions), better: "higher" },
      { label: "Impressions", value: fmt.int(tCurr.impressions), delta: deltaPct(tCurr.impressions, tPrev.impressions), better: "higher" },
      { label: "Clicks",      value: fmt.int(tCurr.clicks),      delta: deltaPct(tCurr.clicks, tPrev.clicks),   better: "higher" },
      { label: "CTR",         value: fmt.pct(ctr),               delta: deltaPct(ctr, ctrPrev),                 better: "higher" },
      { label: "CPC",         value: "$" + cpc.toFixed(2),       delta: deltaPct(cpc, cpcPrev),                 better: "lower" },
    ];

    const container = document.getElementById("kpis");
    container.innerHTML = kpis
      .map((k) => {
        const isUp = k.delta >= 0;
        const good = k.better === "higher" ? isUp : !isUp;
        const cls = good ? "up" : "down";
        const arrow = isUp ? "▲" : "▼";
        return `
          <div class="kpi">
            <span class="kpi-label">${k.label}</span>
            <span class="kpi-value">${k.value}</span>
            <span class="kpi-delta ${cls}">${arrow} ${Math.abs(k.delta).toFixed(1)}% vs prev.</span>
          </div>
        `;
      })
      .join("");
  }

  function renderTrendChart() {
    const ctx = document.getElementById("trendChart").getContext("2d");
    const labels = state.series.map((d) =>
      new Date(d.date).toLocaleDateString(undefined, { month: "short", day: "numeric" })
    );
    const spend = state.series.map((d) => d.spend);
    const revenue = state.series.map((d) => d.revenue);

    const spendGrad = ctx.createLinearGradient(0, 0, 0, 260);
    spendGrad.addColorStop(0, "rgba(79, 124, 255, 0.35)");
    spendGrad.addColorStop(1, "rgba(79, 124, 255, 0)");
    const revGrad = ctx.createLinearGradient(0, 0, 0, 260);
    revGrad.addColorStop(0, "rgba(46, 204, 113, 0.35)");
    revGrad.addColorStop(1, "rgba(46, 204, 113, 0)");

    if (charts.trend) charts.trend.destroy();
    charts.trend = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          { label: "Spend",   data: spend,   borderColor: "#4f7cff", backgroundColor: spendGrad, fill: true, tension: 0.35, borderWidth: 2, pointRadius: 0 },
          { label: "Revenue", data: revenue, borderColor: "#2ecc71", backgroundColor: revGrad,   fill: true, tension: 0.35, borderWidth: 2, pointRadius: 0 },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: "index" },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#161a23",
            borderColor: "#232836",
            borderWidth: 1,
            callbacks: { label: (c) => `${c.dataset.label}: $${c.parsed.y.toLocaleString()}` },
          },
        },
        scales: {
          x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkipPadding: 16 } },
          y: { grid: { color: "#1c2230" }, ticks: { callback: (v) => "$" + (v / 1000).toFixed(0) + "k" } },
        },
      },
    });
  }

  function renderObjectiveChart() {
    const ctx = document.getElementById("objectiveChart").getContext("2d");
    const byObj = {};
    state.campaigns.forEach((c) => { byObj[c.objective] = (byObj[c.objective] || 0) + c.spend; });
    const labels = Object.keys(byObj);
    const values = labels.map((l) => byObj[l]);

    if (charts.objective) charts.objective.destroy();
    charts.objective = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: ["#4f7cff", "#7c5cff", "#2ecc71", "#f5a623", "#ff6b6b"],
          borderColor: "#11141b",
          borderWidth: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "62%",
        plugins: {
          legend: { position: "right", labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true } },
          tooltip: { callbacks: { label: (c) => `${c.label}: $${c.parsed.toLocaleString()}` } },
        },
      },
    });
  }

  function renderAgeGenderChart() {
    const ctx = document.getElementById("ageGenderChart").getContext("2d");
    if (charts.ageGender) charts.ageGender.destroy();
    charts.ageGender = new Chart(ctx, {
      type: "bar",
      data: {
        labels: AGE_BUCKETS,
        datasets: [
          { label: "Male",   data: AGE_GENDER.male,   backgroundColor: "#4f7cff", borderRadius: 6, maxBarThickness: 28 },
          { label: "Female", data: AGE_GENDER.female, backgroundColor: "#ff6bd6", borderRadius: 6, maxBarThickness: 28 },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: "#1c2230" }, ticks: { callback: (v) => v.toLocaleString() } },
        },
      },
    });
  }

  function renderPlacementChart() {
    const ctx = document.getElementById("placementChart").getContext("2d");
    if (charts.placement) charts.placement.destroy();
    charts.placement = new Chart(ctx, {
      type: "bar",
      data: {
        labels: PLACEMENTS.map((p) => p.name),
        datasets: [{
          label: "Spend",
          data: PLACEMENTS.map((p) => p.spend),
          backgroundColor: "#7c5cff",
          borderRadius: 6,
          maxBarThickness: 36,
        }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (c) => `Spend: $${c.parsed.x.toLocaleString()}` } },
        },
        scales: {
          x: { grid: { color: "#1c2230" }, ticks: { callback: (v) => "$" + (v / 1000).toFixed(0) + "k" } },
          y: { grid: { display: false } },
        },
      },
    });
  }

  function renderTable() {
    const tbody = document.getElementById("campaignBody");
    const rows = state.campaigns
      .filter((c) => state.objective === "all" || c.objective === state.objective)
      .filter((c) => c.name.toLowerCase().includes(state.search.toLowerCase()))
      .map((c) => {
        const ctr = (c.clicks / c.impressions) * 100;
        const cpc = c.spend / c.clicks;
        const roas = c.revenue / c.spend;
        return { ...c, ctr, cpc, roas };
      })
      .sort((a, b) => {
        const k = state.sortKey;
        const av = a[k]; const bv = b[k];
        if (typeof av === "string") return state.sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
        return state.sortDir === "asc" ? av - bv : bv - av;
      });

    tbody.innerHTML = rows.map((c) => `
      <tr>
        <td>${escapeHtml(c.name)}</td>
        <td>${c.objective}</td>
        <td><span class="badge ${c.status}">${c.status}</span></td>
        <td class="num">${fmt.money(c.spend)}</td>
        <td class="num">${fmt.int(c.impressions)}</td>
        <td class="num">${fmt.int(c.clicks)}</td>
        <td class="num">${fmt.pct(c.ctr)}</td>
        <td class="num">$${c.cpc.toFixed(2)}</td>
        <td class="num">${fmt.int(c.conversions)}</td>
        <td class="num">${fmt.multi(c.roas)}</td>
      </tr>
    `).join("");
  }

  function renderTopAds() {
    const grid = document.getElementById("adsGrid");
    grid.innerHTML = TOP_ADS.map((ad) => {
      const [c1, c2] = ad.color.split(",");
      return `
        <div class="ad">
          <div class="ad-thumb" style="background: linear-gradient(135deg, ${c1}, ${c2});">${ad.format}</div>
          <div class="ad-body">
            <div class="ad-title">${escapeHtml(ad.title)}</div>
            <div class="ad-meta">${escapeHtml(ad.campaign)}</div>
            <div class="ad-metrics">
              <div class="ad-metric"><span class="label">Spend</span><span class="value">${fmt.money(ad.spend)}</span></div>
              <div class="ad-metric"><span class="label">CTR</span><span class="value">${ad.ctr.toFixed(2)}%</span></div>
              <div class="ad-metric"><span class="label">ROAS</span><span class="value">${ad.roas.toFixed(2)}x</span></div>
            </div>
          </div>
        </div>
      `;
    }).join("");
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  function renderAll() {
    state.series = buildDailySeries(state.range);
    renderKPIs();
    renderTrendChart();
    renderObjectiveChart();
    renderAgeGenderChart();
    renderPlacementChart();
    renderTable();
    renderTopAds();
    document.getElementById("lastUpdated").textContent =
      "Updated " + new Date().toLocaleString();
  }

  // Wire up controls
  document.getElementById("rangeControl").addEventListener("click", (e) => {
    const btn = e.target.closest(".seg-btn");
    if (!btn) return;
    document.querySelectorAll("#rangeControl .seg-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    state.range = Number(btn.dataset.range);
    renderAll();
  });

  document.getElementById("objectiveFilter").addEventListener("change", (e) => {
    state.objective = e.target.value;
    renderObjectiveChart();
    renderTable();
  });

  document.getElementById("campaignSearch").addEventListener("input", (e) => {
    state.search = e.target.value;
    renderTable();
  });

  document.querySelectorAll(".table th[data-sort]").forEach((th) => {
    th.addEventListener("click", () => {
      const key = th.dataset.sort;
      if (state.sortKey === key) state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      else { state.sortKey = key; state.sortDir = "desc"; }
      renderTable();
    });
  });

  renderAll();
})();

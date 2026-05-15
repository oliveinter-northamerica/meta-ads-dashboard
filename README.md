# Meta Ads Dashboard

A self-contained, zero-build dashboard for visualizing Meta (Facebook/Instagram) ad
performance. Open `index.html` in a browser — no installation required.

## Features

- KPI cards: Spend, Revenue, ROAS, Conversions, Impressions, Clicks, CTR, CPC
  with period-over-period deltas
- Spend & Revenue trend chart (filled line)
- Spend by Objective (doughnut)
- Age + Gender audience breakdown (grouped bars)
- Placement performance (horizontal bars)
- Campaigns table with search, sortable columns, and objective filter
- Top performing ads gallery
- 7d / 30d / 90d range selector

## Stack

- Plain HTML / CSS / JavaScript
- [Chart.js 4](https://www.chartjs.org/) loaded via CDN

## Files

- `index.html` — page structure
- `styles.css` — dark-theme styling
- `data.js` — deterministic mock data
- `app.js` — state, rendering, and chart wiring

## Local preview

```sh
python3 -m http.server 8000
# then open http://localhost:8000
```

Or just double-click `index.html`.

## Plugging in real data

`data.js` is the only file that holds mock data. Replace the exports on
`window.MOCK` with values pulled from the Meta Marketing API (or a backend that
fronts it) and `app.js` will render the dashboard unchanged.

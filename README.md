# meta-ads-dashboard

Single-file HTML dashboard that joins **Meta Ads spend** with **Amazon Attribution sales** to compute ROAS per ad. No build step, no server — just open `index.html`.

## How the join works

Amazon doesn't share Meta click IDs and Meta doesn't see Amazon orders, so we bridge them through **Amazon Attribution tags**:

1. In Amazon Attribution, create a unique tag per Meta ad (or ad set).
2. Use the tag's tracking URL as the Meta ad's destination URL.
3. The dashboard pulls Meta spend by `ad_id` and Amazon sales by `tagId`, then joins on the mapping you maintain.

ROAS = Amazon `attributedSales14d` / Meta `spend`.

## Usage

1. Open `index.html` in a browser.
2. Expand **Credentials**, paste your Meta + Amazon tokens, click **Save**. Tokens live in `localStorage` only.
3. Expand **Ad ↔ Tag mapping**, paste your JSON, click **Save**:
   ```json
   [
     { "metaAdId": "120203...", "amazonTagId": "tag_abc123", "label": "Spring Sale Carousel" }
   ]
   ```
4. Pick a date range, choose an Amazon source, click **Pull & join**.

## CORS caveat

- **Meta Graph API** allows browser calls — the live path works out of the box.
- **Amazon Ads API** blocks direct browser calls. Two options:
  - Pick **Paste CSV** as the Amazon source and paste the export from Amazon Attribution → Reports.
  - Or serve `index.html` behind a proxy that adds CORS headers and forwards `/attribution/report` calls.

## Credentials

- **Meta**: Business Manager → System Users → generate token with `ads_read` scope.
- **Amazon**: Amazon Ads API requires LWA OAuth — you'll need an access token, client ID, and profile ID. See [Amazon Ads API docs](https://advertising.amazon.com/API/docs/en-us/reference/2/attribution).

## Why not Next.js?

The earlier scaffold added a framework + build step. This version is one HTML file you can email, host on S3, or open locally. Tradeoff: credentials are in `localStorage` and Amazon API needs a proxy.

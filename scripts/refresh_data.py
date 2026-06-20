"""Refresh scripts/raw/*.json from the Meta Marketing API.

Run by .github/workflows/refresh-data.yml on a daily cron. Mirrors the data
shapes that build_data.py expects, so the existing build pipeline keeps
working unchanged.

Environment variables (set as GitHub Actions secrets):
    META_ACCESS_TOKEN   long-lived Meta user/system-user token with ads_read
    META_AD_ACCOUNT_ID  e.g. act_1354817955224233

Limitations:
    - Only updates the raw JSON inputs for this repo's `scripts/build_data.py`.
    - Does NOT regenerate the production password-protected dashboards
      (meta-amazon.html, meta-combined.html, meta-daily.html) — those are
      produced by a separate local workflow that this scaffold does not yet
      replicate.
    - Amazon data is out of scope here. Add a sibling script
      (scripts/refresh_amazon.py) once the Amazon source is decided
      (SP-API vs. Amazon Ads Attribution vs. Porter export).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.api import FacebookAdsApi

HERE = Path(__file__).resolve().parent
OUT = HERE / "raw"
OUT.mkdir(exist_ok=True)


def fmt_money(v, currency_symbol="₩", currency_code="KRW"):
    return f"{currency_symbol}{int(round(float(v))):,} {currency_code}"


def fmt_int(v):
    return f"{int(v):,}"


def fmt_pct(v):
    return f"{float(v):.2f}%"


def main() -> int:
    token = os.environ.get("META_ACCESS_TOKEN")
    account_id = os.environ.get("META_AD_ACCOUNT_ID")
    if not token or not account_id:
        print("META_ACCESS_TOKEN and META_AD_ACCOUNT_ID must be set.", file=sys.stderr)
        return 2

    FacebookAdsApi.init(access_token=token)
    account = AdAccount(account_id)

    # --- Campaigns: last_30d, top 50 by spend ----------------------------------
    camp_insights = list(
        account.get_insights(
            fields=["campaign_id", "campaign_name", "spend", "impressions", "clicks", "ctr", "cpc", "objective"],
            params={
                "level": "campaign",
                "date_preset": "last_30d",
                "limit": 50,
                "sort": ["spend_descending"],
            },
        )
    )
    # Pull campaign statuses in one batch to mirror the existing schema.
    campaigns = list(account.get_campaigns(fields=["id", "status"]))
    status_by_id = {c["id"]: c.get("status", "UNKNOWN") for c in campaigns}

    raw_campaigns = []
    for r in camp_insights:
        cid = r.get("campaign_id")
        raw_campaigns.append({
            "id": cid,
            "name": r.get("campaign_name", ""),
            "status": status_by_id.get(cid, "UNKNOWN"),
            "objective": r.get("objective", ""),
            "amount_spent": fmt_money(r.get("spend", 0)),
            "impressions": fmt_int(int(r.get("impressions", 0))),
            "clicks": fmt_int(int(r.get("clicks", 0))),
            "ctr": fmt_pct(r.get("ctr", 0)),
            "cpc": fmt_money(r.get("cpc", 0)),
        })

    # --- Timeseries: last_90d, daily, account-level ----------------------------
    ts_insights = list(
        account.get_insights(
            fields=["spend", "impressions", "clicks"],
            params={
                "level": "account",
                "date_preset": "last_90d",
                "time_increment": 1,
            },
        )
    )
    raw_ts = []
    for r in sorted(ts_insights, key=lambda x: x.get("date_start", "")):
        raw_ts.append({
            "amount_spent": fmt_money(r.get("spend", 0)),
            "impressions": fmt_int(int(r.get("impressions", 0))),
            "clicks": fmt_int(int(r.get("clicks", 0))),
            "date_start": r.get("date_start", ""),
        })

    # --- Placements: last_30d, by publisher_platform ---------------------------
    plac_insights = list(
        account.get_insights(
            fields=["spend"],
            params={
                "level": "account",
                "date_preset": "last_30d",
                "breakdowns": ["publisher_platform"],
            },
        )
    )
    raw_plac = [
        {
            "amount_spent": fmt_money(r.get("spend", 0)),
            "publisher_platform": r.get("publisher_platform", "unknown"),
        }
        for r in plac_insights
    ]

    (OUT / "campaigns.json").write_text(json.dumps(raw_campaigns, ensure_ascii=False))
    (OUT / "timeseries.json").write_text(json.dumps(raw_ts, ensure_ascii=False))
    (OUT / "placements.json").write_text(json.dumps(raw_plac, ensure_ascii=False))

    print(
        f"Refreshed: {len(raw_campaigns)} campaigns, {len(raw_ts)} daily rows, "
        f"{len(raw_plac)} placements."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

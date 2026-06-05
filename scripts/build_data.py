"""Transform raw Meta Ads MCP responses into the dashboard's data.js."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
OUT = HERE.parent / "data.js"
AMAZON_OUT = HERE.parent / "amazon-data.js"

ACCOUNT_NAME = "[북미]성분에디터_아마존"
ACCOUNT_ID = "act_1354817955224233"
CURRENCY = "KRW"
GENERATED_AT = "2026-06-04"
DATE_RANGE_LABEL = "May 5 – June 3, 2026 (top 50 by spend)"

# USD→KRW for joint Meta×Amazon ROAS. Update when refreshing data.
USD_KRW = 1380

PLACEMENT_LABEL = {
    "facebook": "Facebook",
    "instagram": "Instagram",
    "messenger": "Messenger",
    "audience_network": "Audience Network",
    "threads": "Threads",
    "unknown": "Other",
}


def parse_money(s: str) -> int:
    return int(re.sub(r"[^\d]", "", s))


def parse_int(s: str) -> int:
    return int(s.replace(",", ""))


def parse_pct(s: str) -> float:
    return float(s.rstrip("%"))


def parse_date(s: str) -> str:
    return datetime.strptime(s, "%B %d, %Y").strftime("%Y-%m-%d")


def js(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def main() -> None:
    raw_campaigns = json.loads((RAW / "campaigns.json").read_text())
    raw_timeseries = json.loads((RAW / "timeseries.json").read_text())
    raw_placements = json.loads((RAW / "placements.json").read_text())

    campaigns = [
        {
            "id": c["id"],
            "name": c["name"].strip(),
            "status": c["status"].title(),
            "objective": c["objective"],
            "spend": parse_money(c["amount_spent"]),
            "impressions": parse_int(c["impressions"]),
            "clicks": parse_int(c["clicks"]),
            "ctr": parse_pct(c["ctr"]),
            "cpc": parse_money(c["cpc"]),
        }
        for c in raw_campaigns
    ]

    timeseries = [
        {
            "date": parse_date(t["date_start"]),
            "spend": parse_money(t["amount_spent"]),
            "impressions": parse_int(t["impressions"]),
            "clicks": parse_int(t["clicks"]),
        }
        for t in raw_timeseries
    ]
    timeseries.sort(key=lambda r: r["date"])

    total_placement_spend = sum(parse_money(p["amount_spent"]) for p in raw_placements)
    placements = sorted(
        [
            {
                "name": PLACEMENT_LABEL.get(p["publisher_platform"], p["publisher_platform"]),
                "spend": parse_money(p["amount_spent"]),
                "share": round(parse_money(p["amount_spent"]) / total_placement_spend * 100, 2),
            }
            for p in raw_placements
        ],
        key=lambda p: -p["spend"],
    )

    meta = {
        "accountName": ACCOUNT_NAME,
        "accountId": ACCOUNT_ID,
        "currency": CURRENCY,
        "generatedAt": GENERATED_AT,
        "dateRange": DATE_RANGE_LABEL,
    }

    body = (
        "// Auto-generated from Meta Ads (via Meta Ads MCP). Do not edit by hand —\n"
        "// re-run scripts/build_data.py with refreshed /tmp/raw_*.json inputs.\n\n"
        f"const meta = {js(meta)};\n\n"
        f"const campaigns = {js(campaigns)};\n\n"
        f"const timeseries = {js(timeseries)};\n\n"
        f"const placements = {js(placements)};\n"
    )

    OUT.write_text(body, encoding="utf-8")
    print(f"Wrote {OUT}: {len(campaigns)} campaigns, {len(timeseries)} daily rows, "
          f"{len(placements)} placements.")

    build_amazon(timeseries)


def build_amazon(meta_timeseries: list[dict]) -> None:
    raw = json.loads((RAW / "amazon_sales.json").read_text())
    amazon_rows = sorted(raw["rows"], key=lambda r: r["date"])

    meta_by_date = {r["date"]: r["spend"] for r in meta_timeseries}
    joint = []
    for row in amazon_rows:
        meta_spend_krw = meta_by_date.get(row["date"], 0)
        sales_krw = row["sales"] * USD_KRW
        roas = (sales_krw / meta_spend_krw) if meta_spend_krw else None
        joint.append(
            {
                "date": row["date"],
                "amazonSales": row["sales"],
                "amazonOrders": row["orders"],
                "amazonUnits": row["units"],
                "metaSpendKrw": meta_spend_krw,
                "amazonSalesKrw": round(sales_krw),
                "roasKrw": round(roas, 2) if roas else None,
            }
        )

    amazon_meta = {
        "marketplace": raw["marketplace"],
        "marketplaceId": raw["marketplaceId"],
        "currency": raw["currency"],
        "source": raw["source"],
        "dataAvailableThrough": raw["dataAvailableThrough"],
        "fetchedAt": raw["fetchedAt"],
        "usdKrw": USD_KRW,
        "rangeStart": joint[0]["date"] if joint else None,
        "rangeEnd": joint[-1]["date"] if joint else None,
    }

    body = (
        "// Auto-generated. Amazon Seller data via Porter Metrics.\n"
        "// USD→KRW rate is hardcoded in scripts/build_data.py — refresh on rebuild.\n\n"
        f"const amazonMeta = {js(amazon_meta)};\n\n"
        f"const amazonDaily = {js(joint)};\n"
    )
    AMAZON_OUT.write_text(body, encoding="utf-8")
    print(f"Wrote {AMAZON_OUT}: {len(joint)} Amazon daily rows ({amazon_meta['rangeStart']} → {amazon_meta['rangeEnd']}).")


if __name__ == "__main__":
    main()

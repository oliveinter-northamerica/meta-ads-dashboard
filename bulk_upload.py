"""Bulk-upload Meta ads from a CSV template.

All entities are created with status=PAUSED so nothing spends money until you
review and activate in Ads Manager.

Env vars required:
  META_ACCESS_TOKEN     long-lived access token with ads_management scope
  META_AD_ACCOUNT_ID    e.g. act_1234567890

Usage:
  python bulk_upload.py template.csv
  python bulk_upload.py template.csv --dry-run
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict

from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.campaign import Campaign
from facebook_business.api import FacebookAdsApi

PAUSED = "PAUSED"


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"No rows in {path}")
    return rows


def group(rows):
    tree = defaultdict(lambda: defaultdict(list))
    campaign_meta = {}
    adset_meta = {}
    for r in rows:
        c, a = r["campaign_name"], r["adset_name"]
        tree[c][a].append(r)
        campaign_meta.setdefault(c, r)
        adset_meta.setdefault((c, a), r)
    return tree, campaign_meta, adset_meta


def special_ad_categories(value):
    if not value or value.strip().upper() == "NONE":
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def build_targeting(row):
    return {
        "geo_locations": {"countries": [c.strip() for c in row["countries"].split(",") if c.strip()]},
        "age_min": int(row["age_min"]),
        "age_max": int(row["age_max"]),
    }


def build_creative_spec(row):
    return {
        "name": f"Creative - {row['ad_name']}",
        "object_story_spec": {
            "page_id": row["page_id"],
            "link_data": {
                "link": row["link_url"],
                "message": row["primary_text"],
                "name": row["headline"],
                "description": row["description"],
                "picture": row["image_url"],
                "call_to_action": {"type": row["cta"], "value": {"link": row["link_url"]}},
            },
        },
    }


def upload(account, tree, campaign_meta, adset_meta, dry_run):
    results = []
    for c_name, adsets in tree.items():
        cm = campaign_meta[c_name]
        c_params = {
            Campaign.Field.name: c_name,
            Campaign.Field.objective: cm["campaign_objective"],
            Campaign.Field.status: PAUSED,
            Campaign.Field.special_ad_categories: special_ad_categories(cm["special_ad_categories"]),
        }
        if dry_run:
            print("CAMPAIGN:", json.dumps(c_params, indent=2))
            campaign_id = f"DRY_CAMPAIGN_{c_name}"
        else:
            campaign = account.create_campaign(params=c_params)
            campaign_id = campaign["id"]
            print(f"Created campaign {campaign_id}: {c_name}")

        for a_name, ads in adsets.items():
            am = adset_meta[(c_name, a_name)]
            as_params = {
                AdSet.Field.name: a_name,
                AdSet.Field.campaign_id: campaign_id,
                AdSet.Field.daily_budget: int(float(am["daily_budget_usd"]) * 100),
                AdSet.Field.billing_event: am["billing_event"],
                AdSet.Field.optimization_goal: am["optimization_goal"],
                AdSet.Field.targeting: build_targeting(am),
                AdSet.Field.status: PAUSED,
            }
            if dry_run:
                print("AD SET:", json.dumps(as_params, indent=2, default=str))
                adset_id = f"DRY_ADSET_{a_name}"
            else:
                adset = account.create_ad_set(params=as_params)
                adset_id = adset["id"]
                print(f"  Created ad set {adset_id}: {a_name}")

            for ad_row in ads:
                creative_spec = build_creative_spec(ad_row)
                if dry_run:
                    print("CREATIVE:", json.dumps(creative_spec, indent=2))
                    creative_id = f"DRY_CREATIVE_{ad_row['ad_name']}"
                else:
                    creative = account.create_ad_creative(params=creative_spec)
                    creative_id = creative["id"]

                ad_params = {
                    Ad.Field.name: ad_row["ad_name"],
                    Ad.Field.adset_id: adset_id,
                    Ad.Field.creative: {"creative_id": creative_id},
                    Ad.Field.status: PAUSED,
                }
                if dry_run:
                    print("AD:", json.dumps(ad_params, indent=2))
                    ad_id = f"DRY_AD_{ad_row['ad_name']}"
                else:
                    ad = account.create_ad(params=ad_params)
                    ad_id = ad["id"]
                    print(f"    Created ad {ad_id}: {ad_row['ad_name']}")

                results.append({"campaign": campaign_id, "adset": adset_id, "ad": ad_id, "name": ad_row["ad_name"]})
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv_path")
    p.add_argument("--dry-run", action="store_true", help="Print payloads without calling the API")
    args = p.parse_args()

    rows = load_rows(args.csv_path)
    tree, campaign_meta, adset_meta = group(rows)

    account = None
    if not args.dry_run:
        token = os.environ.get("META_ACCESS_TOKEN")
        account_id = os.environ.get("META_AD_ACCOUNT_ID")
        if not token or not account_id:
            sys.exit("Set META_ACCESS_TOKEN and META_AD_ACCOUNT_ID env vars (or use --dry-run).")
        FacebookAdsApi.init(access_token=token)
        account = AdAccount(account_id)

    results = upload(account, tree, campaign_meta, adset_meta, args.dry_run)
    print(f"\nDone. {len(results)} ad(s) staged as PAUSED.")
    if not args.dry_run:
        print("Review in Ads Manager before activating.")


if __name__ == "__main__":
    main()

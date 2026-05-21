"""Bulk-upload Meta ads from a CSV or XLSX template.

All entities are created with status=PAUSED so nothing spends money until you
review and activate in Ads Manager.

Env vars required:
  META_ACCESS_TOKEN     long-lived access token with ads_management scope
  META_AD_ACCOUNT_ID    e.g. act_1234567890

Usage:
  python bulk_upload.py template.csv
  python bulk_upload.py template.xlsx
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
    if path.lower().endswith(".xlsx"):
        from openpyxl import load_workbook

        wb = load_workbook(path, data_only=True)
        ws = wb.active
        it = ws.iter_rows(values_only=True)
        headers = [str(h) if h is not None else "" for h in next(it)]
        rows = []
        for raw in it:
            if all(v is None or v == "" for v in raw):
                continue
            rows.append({h: ("" if v is None else str(v)) for h, v in zip(headers, raw)})
    else:
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


def build_targeting(row, dry_run=False):
    saved_id = (row.get("saved_audience_id") or "").strip()
    if saved_id:
        if dry_run:
            return {"saved_audience_id": saved_id}
        from facebook_business.adobjects.savedaudience import SavedAudience

        sa = SavedAudience(saved_id).api_get(fields=["targeting"])
        targeting = sa.get("targeting")
        if not targeting:
            sys.exit(f"Saved audience {saved_id} has no targeting spec — open it in Ads Manager and check it has a location.")
        return targeting
    return {
        "geo_locations": {"countries": [c.strip() for c in row["countries"].split(",") if c.strip()]},
        "age_min": int(row["age_min"]),
        "age_max": int(row["age_max"]),
    }


def _get(row, key, default=""):
    return (row.get(key) or default).strip() if isinstance(row.get(key), str) else (row.get(key) or default)


def build_campaign_params(row, name):
    params = {
        Campaign.Field.name: name,
        Campaign.Field.objective: row["campaign_objective"],
        Campaign.Field.status: PAUSED,
        Campaign.Field.special_ad_categories: special_ad_categories(row.get("special_ad_categories", "")),
        "is_adset_budget_sharing_enabled": False,
    }
    buying = _get(row, "buying_type")
    if buying:
        params[Campaign.Field.buying_type] = buying
    return params


def build_adset_params(row, name, campaign_id, dry_run):
    bid_strategy = _get(row, "bid_strategy") or "LOWEST_COST_WITHOUT_CAP"
    params = {
        AdSet.Field.name: name,
        AdSet.Field.campaign_id: campaign_id,
        AdSet.Field.daily_budget: int(float(row["daily_budget_usd"]) * 100),
        AdSet.Field.billing_event: row["billing_event"],
        AdSet.Field.optimization_goal: row["optimization_goal"],
        AdSet.Field.bid_strategy: bid_strategy,
        AdSet.Field.targeting: build_targeting(row, dry_run=dry_run),
        AdSet.Field.status: PAUSED,
    }
    bid_amount = _get(row, "bid_amount_usd")
    if bid_amount:
        params[AdSet.Field.bid_amount] = int(float(bid_amount) * 100)
    destination = _get(row, "destination_type")
    if destination:
        params[AdSet.Field.destination_type] = destination
    start = _get(row, "start_time")
    if start:
        params[AdSet.Field.start_time] = start
    end = _get(row, "end_time")
    if end:
        params[AdSet.Field.end_time] = end
    pixel_id = _get(row, "pixel_id")
    event_type = _get(row, "custom_event_type")
    if pixel_id and event_type:
        params[AdSet.Field.promoted_object] = {"pixel_id": pixel_id, "custom_event_type": event_type}
    elif pixel_id:
        params[AdSet.Field.promoted_object] = {"pixel_id": pixel_id}
    return params


def build_creative_spec(row):
    link_data = {
        "link": row["link_url"],
        "message": row["primary_text"],
        "name": row["headline"],
        "description": row["description"],
        "picture": row["image_url"],
        "call_to_action": {"type": row["cta"], "value": {"link": row["link_url"]}},
    }
    spec = {
        "name": f"Creative - {row['ad_name']}",
        "object_story_spec": {
            "page_id": row["page_id"],
            "link_data": link_data,
        },
    }
    instagram_actor = _get(row, "instagram_actor_id")
    if instagram_actor:
        spec["object_story_spec"]["instagram_user_id"] = instagram_actor
    url_tags = _get(row, "url_tags")
    if url_tags:
        spec["url_tags"] = url_tags
    return spec


def _cleanup(created, account):
    """On failure, delete entities we created during this run so the user
    doesn't have to manually clean up orphan campaigns / ad sets / ads."""
    for kind, obj_id in reversed(created):
        try:
            if kind == "ad":
                Ad(obj_id).api_delete()
            elif kind == "adset":
                AdSet(obj_id).api_delete()
            elif kind == "campaign":
                Campaign(obj_id).api_delete()
            print(f"  Cleaned up {kind} {obj_id}")
        except Exception as exc:
            print(f"  Failed to clean up {kind} {obj_id}: {exc}")


def upload(account, tree, campaign_meta, adset_meta, dry_run):
    results = []
    created = []
    try:
        for c_name, adsets in tree.items():
            cm = campaign_meta[c_name]
            c_params = build_campaign_params(cm, c_name)
            if dry_run:
                print("CAMPAIGN:", json.dumps(c_params, indent=2))
                campaign_id = f"DRY_CAMPAIGN_{c_name}"
            else:
                campaign = account.create_campaign(params=c_params)
                campaign_id = campaign["id"]
                created.append(("campaign", campaign_id))
                print(f"Created campaign {campaign_id}: {c_name}")

            for a_name, ads in adsets.items():
                am = adset_meta[(c_name, a_name)]
                as_params = build_adset_params(am, a_name, campaign_id, dry_run)
                if dry_run:
                    print("AD SET:", json.dumps(as_params, indent=2, default=str))
                    adset_id = f"DRY_ADSET_{a_name}"
                else:
                    adset = account.create_ad_set(params=as_params)
                    adset_id = adset["id"]
                    created.append(("adset", adset_id))
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
                        created.append(("ad", ad_id))
                        print(f"    Created ad {ad_id}: {ad_row['ad_name']}")

                    results.append({"campaign": campaign_id, "adset": adset_id, "ad": ad_id, "name": ad_row["ad_name"]})
    except Exception:
        if not dry_run and created:
            print("\nUpload failed mid-flight — rolling back created entities:")
            _cleanup(created, account)
        raise
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

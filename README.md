# meta-ads-dashboard

Bulk-upload Meta (Facebook/Instagram) ads from a CSV. Everything is created as
**PAUSED** so you can review in Ads Manager before activating — nothing spends
money until you flip the switch.

## Setup

```bash
pip install -r requirements.txt
export META_ACCESS_TOKEN=...        # token with ads_management scope
export META_AD_ACCOUNT_ID=act_...   # ad account ID, with the act_ prefix
```

## Usage

1. Copy `template.csv` and fill in one row per ad. Rows sharing a
   `campaign_name` are grouped into one campaign; rows sharing
   `campaign_name` + `adset_name` are grouped into one ad set.
2. Preview without calling the API:
   ```bash
   python bulk_upload.py template.csv --dry-run
   ```
3. Upload (still PAUSED):
   ```bash
   python bulk_upload.py template.csv
   ```
4. Review in Ads Manager, then activate the campaigns/ad sets/ads you want
   to run.

## CSV columns

| Column | Notes |
| --- | --- |
| `campaign_name` | Group key for campaigns |
| `campaign_objective` | e.g. `OUTCOME_TRAFFIC`, `OUTCOME_SALES`, `OUTCOME_ENGAGEMENT` |
| `special_ad_categories` | `NONE` or comma-separated list (`HOUSING`, `CREDIT`, …) |
| `adset_name` | Group key for ad sets within a campaign |
| `daily_budget_usd` | Dollars, converted to cents for the API |
| `billing_event` | Usually `IMPRESSIONS` |
| `optimization_goal` | e.g. `LINK_CLICKS`, `OFFSITE_CONVERSIONS`, `REACH` |
| `countries` | Comma-separated ISO codes (`US,CA`) |
| `age_min`, `age_max` | Integers |
| `page_id` | Facebook Page ID the ad runs from |
| `ad_name` | Unique-ish per ad set |
| `image_url` | Publicly reachable image URL |
| `primary_text` | Body copy |
| `headline` | Headline |
| `description` | Link description |
| `link_url` | Landing page |
| `cta` | e.g. `SHOP_NOW`, `LEARN_MORE`, `SIGN_UP` |

## Safety

- Every campaign, ad set, and ad is created with `status=PAUSED`.
- Use `--dry-run` first to inspect the exact payloads.
- The script never deletes or modifies existing entities — it only creates new ones.

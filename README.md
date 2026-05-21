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

## Usage — Web UI (recommended)

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000 (in a Codespace, the **Ports** tab gives you a
forwarded URL — click it). The page walks you through three steps:

1. **Download** `template.xlsx` (button on the page) — open in Excel/Sheets,
   fill rows using the dropdowns, save.
2. **Upload** the filled file.
3. Paste your **Access token** and **Ad account ID**, leave "Dry run" ticked
   for a preview, then submit. Untick "Dry run" when you're ready to
   actually create the ads in Meta.

Results page lists the campaign / ad set / ad IDs that were created (all
PAUSED) with a link to Ads Manager.

## Usage — CLI

Same flow without the browser:
   ```bash
   python generate_template.py
   ```
   This writes `template.xlsx`. Open in Excel/Sheets — clicking an enum cell
   (objective, optimization goal, CTA, etc.) shows a dropdown of valid values.
   Or skip this and edit `template.csv` directly.
2. Fill in one row per ad. Rows sharing a `campaign_name` are grouped into
   one campaign; rows sharing `campaign_name` + `adset_name` are grouped into
   one ad set.
3. Preview without calling the API:
   ```bash
   python bulk_upload.py template.xlsx --dry-run
   ```
4. Upload (still PAUSED):
   ```bash
   python bulk_upload.py template.xlsx
   ```
5. Review in Ads Manager, then activate the campaigns/ad sets/ads you want
   to run.

## Columns

| Column | Notes |
| --- | --- |
| `campaign_name` | Group key for campaigns |
| `campaign_objective` | Dropdown: `OUTCOME_AWARENESS`, `OUTCOME_TRAFFIC`, `OUTCOME_ENGAGEMENT`, `OUTCOME_LEADS`, `OUTCOME_APP_PROMOTION`, `OUTCOME_SALES` |
| `special_ad_categories` | Dropdown: `NONE`, `HOUSING`, `CREDIT`, `EMPLOYMENT`, `ISSUES_ELECTIONS_POLITICS`, `ONLINE_GAMBLING_AND_GAMING`, `FINANCIAL_PRODUCTS_SERVICES` |
| `adset_name` | Group key for ad sets within a campaign |
| `daily_budget_usd` | Dollars (converted to cents for the API) |
| `billing_event` | Dropdown: `IMPRESSIONS`, `LINK_CLICKS`, `POST_ENGAGEMENT`, `VIDEO_VIEWS`, `THRUPLAY` |
| `optimization_goal` | Dropdown: `REACH`, `IMPRESSIONS`, `LINK_CLICKS`, `LANDING_PAGE_VIEWS`, `POST_ENGAGEMENT`, `PAGE_LIKES`, `VIDEO_VIEWS`, `THRUPLAY`, `OFFSITE_CONVERSIONS`, `VALUE`, `LEAD_GENERATION`, `QUALITY_LEAD`, `CONVERSATIONS`, `APP_INSTALLS`, `AD_RECALL_LIFT` |
| `saved_audience_id` | Optional. Paste a Saved Audience ID from Ads Manager → Audiences. When set, the script uses this audience and ignores `countries`/`age_min`/`age_max`. |
| `countries` | Comma-separated ISO codes (`US,CA`). Used only when `saved_audience_id` is empty. |
| `age_min`, `age_max` | Integers. Used only when `saved_audience_id` is empty. |
| `page_id` | Facebook Page ID the ad runs from |
| `ad_name` | Unique-ish per ad set |
| `image_url` | Publicly reachable image URL |
| `primary_text` | Body copy |
| `headline` | Headline |
| `description` | Link description |
| `link_url` | Landing page |
| `cta` | Dropdown: `SHOP_NOW`, `LEARN_MORE`, `SIGN_UP`, `SUBSCRIBE`, `DOWNLOAD`, `BOOK_TRAVEL`, `CONTACT_US`, `GET_OFFER`, `GET_QUOTE`, `APPLY_NOW`, `ORDER_NOW`, `DONATE_NOW`, `INSTALL_APP`, `USE_APP`, `WATCH_MORE`, `LISTEN_NOW`, `SEND_MESSAGE`, `MESSAGE_PAGE`, `GET_DIRECTIONS`, `CALL_NOW`, `NO_BUTTON` |

### Finding your Saved Audience ID

In Ads Manager → **Audiences**, click a saved audience. The URL contains
`...?audience_id=23851234567890123` — that number is the ID to paste into
the `saved_audience_id` column.

## Safety

- Every campaign, ad set, and ad is created with `status=PAUSED`.
- Use `--dry-run` first to inspect the exact payloads.
- The script never deletes or modifies existing entities — it only creates new ones.

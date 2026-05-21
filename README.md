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

### Campaign

| Column | Required? | Notes |
| --- | --- | --- |
| `campaign_name` | yes | Group key — rows sharing this become one campaign |
| `campaign_objective` | yes | Dropdown: `OUTCOME_AWARENESS`, `OUTCOME_TRAFFIC`, `OUTCOME_ENGAGEMENT`, `OUTCOME_LEADS`, `OUTCOME_APP_PROMOTION`, `OUTCOME_SALES` |
| `buying_type` | yes | Dropdown: `AUCTION` (default), `RESERVED` |
| `special_ad_categories` | yes | Dropdown: `NONE`, `HOUSING`, `CREDIT`, `EMPLOYMENT`, `ISSUES_ELECTIONS_POLITICS`, `ONLINE_GAMBLING_AND_GAMING`, `FINANCIAL_PRODUCTS_SERVICES` |
| `campaign_daily_budget_usd` | CBO | Set to use Campaign Budget Optimization. Mutually exclusive with `campaign_lifetime_budget_usd`. When either is set, ad-set `daily_budget_usd` / `lifetime_budget_usd` MUST be blank. |
| `campaign_lifetime_budget_usd` | CBO | CBO lifetime budget. Mutually exclusive with `campaign_daily_budget_usd`. |
| `campaign_bid_strategy` | CBO | Dropdown: same values as `bid_strategy`. Only used when a campaign budget is set. |
| `campaign_spend_cap_usd` | optional | Total spend cap for the campaign (dollars). |
| `campaign_start_time` | optional | ISO 8601 (e.g. `2026-06-01T09:00:00-0700`). |
| `campaign_stop_time` | optional | ISO 8601. |

### Ad set

| Column | Required? | Notes |
| --- | --- | --- |
| `adset_name` | yes | Group key — rows sharing campaign + adset name become one ad set |
| `daily_budget_usd` | ABO | Dollars. Required for ABO. Leave blank if the parent campaign uses CBO. Mutually exclusive with `lifetime_budget_usd`. |
| `lifetime_budget_usd` | ABO | Dollars. Lifetime alternative to `daily_budget_usd`. Requires `end_time`. |
| `bid_strategy` | ABO | Dropdown: `LOWEST_COST_WITHOUT_CAP` (default), `LOWEST_COST_WITH_BID_CAP`, `COST_CAP`, `LOWEST_COST_WITH_MIN_ROAS`. Ignored under CBO. |
| `bid_amount_usd` | conditional | Required if `bid_strategy` is `LOWEST_COST_WITH_BID_CAP` or `COST_CAP`. Dollars. |
| `bid_roas_floor` | conditional | Required if `bid_strategy` is `LOWEST_COST_WITH_MIN_ROAS`. Decimal multiple (`2.0` = 2.0x ROAS floor). |
| `daily_spend_cap_usd` | optional | Per-day spend cap on the ad set. |
| `lifetime_spend_cap_usd` | optional | Lifetime spend cap on the ad set. |
| `pacing_type` | optional | Dropdown: `standard` (default), `no_pacing`. |
| `billing_event` | yes | Dropdown: `IMPRESSIONS`, `LINK_CLICKS`, `POST_ENGAGEMENT`, `VIDEO_VIEWS`, `THRUPLAY` |
| `optimization_goal` | yes | Dropdown: `REACH`, `IMPRESSIONS`, `LINK_CLICKS`, `LANDING_PAGE_VIEWS`, `POST_ENGAGEMENT`, `PAGE_LIKES`, `VIDEO_VIEWS`, `THRUPLAY`, `OFFSITE_CONVERSIONS`, `VALUE`, `LEAD_GENERATION`, `QUALITY_LEAD`, `CONVERSATIONS`, `APP_INSTALLS`, `AD_RECALL_LIFT` |
| `destination_type` | yes for most | Dropdown: `WEBSITE` (most common), `APP`, `MESSENGER`, `INSTAGRAM_DIRECT`, `WHATSAPP`, `FACEBOOK`, `ON_AD`, `ON_POST`, `ON_PAGE`, `ON_EVENT`, `ON_VIDEO`, `SHOP_AUTOMATIC` |
| `start_time` | optional | ISO 8601 (e.g. `2026-06-01T09:00:00-0700`). Blank = start immediately. |
| `end_time` | optional | ISO 8601. Required with `lifetime_budget_usd`. Blank = run indefinitely. |
| `pixel_id` | conditional | Required for `OUTCOME_SALES` + `OFFSITE_CONVERSIONS`/`VALUE`. Your Meta Pixel ID. |
| `custom_event_type` | conditional | Dropdown: `PURCHASE`, `LEAD`, `COMPLETE_REGISTRATION`, `ADD_TO_CART`, `INITIATE_CHECKOUT`, `ADD_PAYMENT_INFO`, `VIEW_CONTENT`, `SEARCH`, `SUBSCRIBE`, `CONTACT`, `DONATE`, `OTHER`. Pair with `pixel_id`. |
| `application_id` | conditional | Required for `OUTCOME_APP_PROMOTION`. The Meta App ID. |
| `object_store_url` | conditional | Required for `OUTCOME_APP_PROMOTION`. The App Store / Play Store URL. |
| `dsa_beneficiary` | conditional | Required when targeting EU countries (Digital Services Act). |
| `dsa_payor` | conditional | Required when targeting EU countries. |

### Targeting (one ad set's audience)

| Column | Required? | Notes |
| --- | --- | --- |
| `saved_audience_id` | use this **or** the rows below | Paste a Saved Audience ID from Ads Manager → Audiences. When set, the script fetches its full targeting spec and uses that — every other targeting column is ignored. |
| `countries` | required if no saved audience | Comma-separated ISO codes (`US,CA`) |
| `age_min`, `age_max` | required if no saved audience | Integers (13–65) |
| `genders` | optional | Dropdown: blank (all), `1` (male), `2` (female), `1,2` (both, explicit). |
| `included_custom_audience_ids` | optional | Comma-separated custom audience IDs to include. |
| `excluded_custom_audience_ids` | optional | Comma-separated custom audience IDs to exclude. |

### Ad / creative

| Column | Required? | Notes |
| --- | --- | --- |
| `page_id` | yes | Facebook Page ID the ad runs from. Must be connected to the ad account. |
| `instagram_actor_id` | optional | Instagram account ID to also run the ad from. Blank = Facebook only. |
| `ad_name` | yes | Unique within an ad set |
| `image_url` | image OR video | Publicly fetchable image URL. Drive sharing links don't work — use Imgur, your CDN, S3, etc. Used as the video thumbnail when `video_id` is also set. |
| `video_id` | image OR video | Meta video ID for a video ad. When set, the ad becomes a video ad instead of a static image ad. |
| `primary_text` | yes | Body copy above the ad |
| `headline` | yes | Headline below the image / video title |
| `description` | yes (image ads) | Link description (small grey text under the headline). Ignored for video ads. |
| `link_url` | yes | Landing page URL |
| `url_tags` | optional | UTM query params, e.g. `utm_source=facebook&utm_medium=cpc&utm_campaign=spring`. Auto-appended to clicks. |
| `cta` | yes | Dropdown: `SHOP_NOW`, `LEARN_MORE`, `SIGN_UP`, `SUBSCRIBE`, `DOWNLOAD`, `BOOK_TRAVEL`, `CONTACT_US`, `GET_OFFER`, `GET_QUOTE`, `APPLY_NOW`, `ORDER_NOW`, `DONATE_NOW`, `INSTALL_APP`, `USE_APP`, `WATCH_MORE`, `LISTEN_NOW`, `SEND_MESSAGE`, `MESSAGE_PAGE`, `GET_DIRECTIONS`, `CALL_NOW`, `NO_BUTTON` |
| `conversion_domain` | optional | The domain conversions are attributed to (e.g. `example.com`). Recommended for `OUTCOME_SALES`. |

### Finding your Saved Audience ID

In Ads Manager → **Audiences**, click a saved audience. The URL contains
`...?audience_id=23851234567890123` — that number is the ID to paste into
the `saved_audience_id` column.

## Safety

- Every campaign, ad set, and ad is created with `status=PAUSED`.
- Use `--dry-run` (or the Dry-run checkbox in the web UI) first to inspect the exact payloads.
- **Rollback on failure**: if any step fails partway through a real upload, the script deletes the campaign / ad sets / ads it created in that run so you don't get orphan entities in Ads Manager.
- The script never modifies entities it didn't create.

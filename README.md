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

## Usage — Google Sheets (no file download)

Skip the download/upload round-trip — keep everything in a Google Sheet:

1. Copy `template.xlsx` into Google Sheets (File → Import in Sheets, or just paste the headers from `template.csv`).
2. Fill rows.
3. Click **Share** (top-right) → switch access to **Anyone with the link → Viewer**.
4. Copy the URL (something like `https://docs.google.com/spreadsheets/d/SHEET_ID/edit#gid=0`).
5. Paste it into the **Google Sheets URL** field in the web UI, or pass it to the CLI:
   ```bash
   python bulk_upload.py "https://docs.google.com/spreadsheets/d/SHEET_ID/edit#gid=0"
   ```
6. Same dry-run / live behavior as a file upload. The `gid` in the URL selects the tab.

By default the fetch is limited to the cell range `A1:CB5000` (~80 columns × 5000 rows — comfortably covers the template). If your sheet has more rows, add a `range` parameter to the URL:

```
https://docs.google.com/spreadsheets/d/SHEET_ID/edit?range=A1:CB10000#gid=0
```

This keeps Google from evaluating cells outside the range, which is what makes formula-heavy / `IMPORTRANGE` sheets time out. Narrower ranges fetch dramatically faster.

The sheet must be shared publicly with link-viewer access because the script reads it via Google's public CSV export endpoint (no OAuth). If you need to keep the sheet private, fall back to downloading as XLSX/CSV and uploading the file.

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
| `existing_campaign_id` | optional | If set, skip campaign creation and attach new ad sets under this existing campaign. All other campaign columns on the row are ignored. Get the ID from the Ads Manager URL or Business Suite. |
| `campaign_name` | yes | Group key — rows sharing this become one campaign |
| `campaign_objective` | yes | Dropdown: `OUTCOME_AWARENESS`, `OUTCOME_TRAFFIC`, `OUTCOME_ENGAGEMENT`, `OUTCOME_LEADS`, `OUTCOME_APP_PROMOTION`, `OUTCOME_SALES` |
| `buying_type` | yes | Dropdown: `AUCTION` (default), `RESERVED` |
| `special_ad_categories` | yes | Dropdown: `NONE`, `HOUSING`, `CREDIT`, `EMPLOYMENT`, `ISSUES_ELECTIONS_POLITICS`, `ONLINE_GAMBLING_AND_GAMING`, `FINANCIAL_PRODUCTS_SERVICES` |
| `campaign_daily_budget` | CBO | Set to use Campaign Budget Optimization. Mutually exclusive with `campaign_lifetime_budget`. When either is set, ad-set `daily_budget` / `lifetime_budget` MUST be blank. Amount is **in the ad account's currency** (50 = $50 on a USD account, 50000 = 50,000 won on a KRW account). |
| `campaign_lifetime_budget` | CBO | CBO lifetime budget. Same currency rule. Mutually exclusive with `campaign_daily_budget`. |
| `campaign_bid_strategy` | CBO | Dropdown: same values as `bid_strategy`. Only used when a campaign budget is set. |
| `campaign_spend_cap` | optional | Total spend cap for the campaign, in the ad account's currency. |
| `campaign_start_time` | optional | ISO 8601 (e.g. `2026-06-01T09:00:00-0700`). |
| `campaign_stop_time` | optional | ISO 8601. |

### Ad set

| Column | Required? | Notes |
| --- | --- | --- |
| `existing_adset_id` | optional | If set, skip ad set creation and attach new ads under this existing ad set. All other ad-set columns on the row are ignored. |
| `adset_name` | yes | Group key — rows sharing campaign + adset name become one ad set |
| `daily_budget` | ABO | Amount in the ad account's currency (50 = $50 USD, 50000 = 50,000 KRW). Required for ABO. Leave blank if the parent campaign uses CBO. Mutually exclusive with `lifetime_budget`. |
| `lifetime_budget` | ABO | Lifetime alternative to `daily_budget`. Same currency rule. Requires `end_time`. |
| `bid_strategy` | ABO | Dropdown: `LOWEST_COST_WITHOUT_CAP` (default), `LOWEST_COST_WITH_BID_CAP`, `COST_CAP`, `LOWEST_COST_WITH_MIN_ROAS`. Ignored under CBO. |
| `bid_amount` | conditional | Required if `bid_strategy` is `LOWEST_COST_WITH_BID_CAP` or `COST_CAP`. Amount in the ad account's currency. |
| `bid_roas_floor` | conditional | Required if `bid_strategy` is `LOWEST_COST_WITH_MIN_ROAS`. Decimal multiple (`2.0` = 2.0x ROAS floor) — NOT currency. |
| `daily_spend_cap` | optional | Per-day spend cap on the ad set, in the ad account's currency. |
| `lifetime_spend_cap` | optional | Lifetime spend cap on the ad set, in the ad account's currency. |
| `pacing_type` | optional | Dropdown: `standard` (default), `no_pacing`. |
| `billing_event` | yes | Dropdown: `IMPRESSIONS`, `LINK_CLICKS`, `POST_ENGAGEMENT`, `VIDEO_VIEWS`, `THRUPLAY` |
| `optimization_goal` | yes | Dropdown: `REACH`, `IMPRESSIONS`, `LINK_CLICKS`, `LANDING_PAGE_VIEWS`, `POST_ENGAGEMENT`, `PAGE_LIKES`, `VIDEO_VIEWS`, `THRUPLAY`, `OFFSITE_CONVERSIONS`, `VALUE`, `LEAD_GENERATION`, `QUALITY_LEAD`, `CONVERSATIONS`, `APP_INSTALLS`, `AD_RECALL_LIFT` |
| `destination_type` | yes for most | Dropdown: `WEBSITE` (most common), `APP`, `MESSENGER`, `INSTAGRAM_DIRECT`, `WHATSAPP`, `FACEBOOK`, `ON_AD`, `ON_POST`, `ON_PAGE`, `ON_EVENT`, `ON_VIDEO`, `SHOP_AUTOMATIC` |
| `start_time` | optional | ISO 8601 (e.g. `2026-06-01T09:00:00-0700`). Blank = start immediately. |
| `end_time` | optional | ISO 8601. Required with `lifetime_budget`. Blank = run indefinitely. |
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
| `instagram_user_id` | optional | Instagram Business Account ID to also run the ad from. Blank = Facebook only. Not the same as the Page ID — fetch via `GET <page_id>?fields=instagram_business_account` in the Graph Explorer. |
| `threads_user_id` | optional | Threads profile ID to also run the ad from. |
| `ad_name` | yes | Unique within an ad set |
| `existing_post_id` | optional | Promote an existing post from **your own Page** instead of creating a new creative. Paste the numeric Post ID (script combines with this row's `page_id`), or the full `PAGE_ID_POST_ID` form. Mutually exclusive with `partnership_ad_code`. The post supplies the image/video/body text — `image_url`, `video_id`, `primary_text`, `headline`, `description`, `display_link`, `browser_addon`, `phone_number` on this row are ignored. **But `link_url` and `cta` still apply** — they override the post's destination URL and call-to-action button on the rendered ad. |
| `partnership_ad_code` | optional | Run a post from a **partner Page** (Branded Content / Partnership Ad) using the ad code they shared with you. Same content/link/cta rules as `existing_post_id`. Your `page_id` on the row is automatically used as the sponsor identity unless overridden by the columns below. **Shortcut for Paid Partnership Posts**: set `page_id` AND `instagram_user_id` both to the literal word `influencer` (any case) and the script treats the row as a partnership post — it substitutes the sponsor identity from `second_identity_page_id` / `second_identity_ig_id`, requires `partnership_ad_code`, and ignores `image_url` / `video_id` / `video_url` / `primary_text` / `headline` / `description` (the partner's post supplies them). `link_url` + `cta` still override the post's destination. |
| `second_identity_page_id` | optional | Only used with `partnership_ad_code`. The Facebook Page that appears as the **Second identity** in Ads Manager (your brand, the paid partner). Defaults to the row's `page_id` if blank. |
| `second_identity_ig_id` | optional | Only used with `partnership_ad_code`. The Instagram profile that appears as the Second identity's IG handle. Defaults to the row's `instagram_user_id` if blank. |
| `identity_display` | optional | Only used with `partnership_ad_code`. Dropdown: blank / `DYNAMIC` (Meta picks the header that performs best — recommended), `BOTH` (both identities in the header), `FIRST_ONLY` (only the creator's identity in the header). |
| `image_url` | image OR video | Publicly fetchable image URL. **Google Drive links** in any of the standard formats (`drive.google.com/file/d/<ID>/view`, `?id=<ID>`, etc.) are auto-converted to the `lh3.googleusercontent.com/d/<ID>` form that Meta can actually fetch. Used as the video thumbnail when `video_id` is also set. |
| `video_id` | image OR video | Meta video ID for a video ad. Use this if you already uploaded the video to your ad account's media library. When set, the ad becomes a video ad instead of a static image ad. |
| `video_url` | image OR video | Alternative to `video_id` — paste any public video URL (Drive links auto-converted, same as `image_url`). The script uploads it to `/act_<id>/advideos` and uses the resulting video_id. Mutually exclusive with `video_id`. |
| `primary_text` | yes | Body copy above the ad. **Multiple variants:** separate with `\|\|` (double pipe — e.g. `Buy now!\|\|Limited time!`) and the script switches the creative to `asset_feed_spec` so Meta can A/B test them. A single `\|` in your copy is preserved as-is. |
| `headline` | yes | Headline below the image / video title. Same `\|\|`-separation rule for variants. |
| `description` | yes (image ads) | Link description (small grey text under the headline). Same `\|\|`-separation rule for variants. Ignored for video ads. |
| `link_url` | yes | Landing page URL |
| `display_link` | optional | The URL displayed on the ad (cleaner than `link_url`, e.g. `example.com` while `link_url` is a long tracking URL). |
| `url_tags` | optional | UTM query params, e.g. `utm_source=facebook&utm_medium=cpc&utm_campaign=spring`. Auto-appended to clicks. |
| `cta` | yes | Dropdown: `SHOP_NOW`, `LEARN_MORE`, `SIGN_UP`, `SUBSCRIBE`, `DOWNLOAD`, `BOOK_TRAVEL`, `CONTACT_US`, `GET_OFFER`, `GET_QUOTE`, `APPLY_NOW`, `ORDER_NOW`, `DONATE_NOW`, `INSTALL_APP`, `USE_APP`, `WATCH_MORE`, `LISTEN_NOW`, `SEND_MESSAGE`, `MESSAGE_PAGE`, `GET_DIRECTIONS`, `CALL_NOW`, `NO_BUTTON`. Overridden by `browser_addon` when that is set to anything other than blank/`NONE`. |
| `browser_addon` | optional | Dropdown: blank or `NONE` (use `cta` as-is — this is what you want for a normal Website ad). **Warning**: setting `CALL` / `MESSENGER` / `WHATSAPP` does NOT add a button overlay on a Website ad — it **replaces the entire destination**, turning the ad into a click-to-call / click-to-Messenger / click-to-WhatsApp ad. The website URL and the chosen `cta` are both overridden. The "Browser add-on" button overlay you may have seen in Ads Manager is a UI-only feature and isn't exposed via the Marketing API; if you want that, leave this column blank and toggle it manually in Ads Manager after upload. `CALL` and `WHATSAPP` also require `phone_number`. |
| `phone_number` | conditional | Required when `browser_addon` is `CALL` or `WHATSAPP`. For WhatsApp use international format without `+` (e.g. `15551234567`). |
| `conversion_domain` | optional | The domain conversions are attributed to (e.g. `example.com`). Recommended for `OUTCOME_SALES`. |
| `advantage_plus_creative` | optional | **Master switch** for Advantage+ creative. Dropdown: blank (Meta's account default), `ON`, `OFF`. Sets a baseline for `IG_VIDEO_NATIVE_SUBTITLE`, `IMAGE_ANIMATION`, and `TEXT_OVERLAY_TRANSLATION`. The per-feature columns below override this baseline for specific features. |

**Per-feature columns**: dropdown is blank (don't touch) / `ON` / `OFF`. The template carries a column for every toggle visible in Ads Manager's Advantage+ creative section. At upload time the script only forwards the ones Meta currently exposes via the Marketing API; the rest are silently skipped with a one-line note like `Note: 3 adv_* setting(s) skipped (UI-only, not exposed in Marketing API): adv_music, adv_enhance_cta, adv_brightness_contrast. Configure manually in Ads Manager after upload.`

Forwarded to the API (Universal — work on most ads):
| Column | API key | UI label |
| --- | --- | --- |
| `adv_ig_video_subtitle` | `IG_VIDEO_NATIVE_SUBTITLE` | IG auto-subtitles (video only) |
| `adv_image_animation` | `IMAGE_ANIMATION` | Add animation |
| `adv_profile_card` | `PROFILE_CARD` | Profile card |
| `adv_text_overlay_translation` | `TEXT_OVERLAY_TRANSLATION` | Translate text overlays |

Forwarded to the API (Catalog-only — only valid on ads connected to a product catalog):
| Column | API key | UI label |
| --- | --- | --- |
| `adv_product_browsing` | `PRODUCT_BROWSING` | Product browsing |
| `adv_product_metadata` | `PRODUCT_METADATA_AUTOMATION` | Product metadata automation |
| `adv_catalog_enhancements` | `STANDARD_ENHANCEMENTS_CATALOG` | Standard enhancements (catalog) |

UI-only — silently skipped at upload, configure manually in Ads Manager:
| Column | UI label |
| --- | --- |
| `adv_add_overlays` | Add overlays |
| `adv_image_touchups` | Visual touch-ups |
| `adv_music` | Add music |
| `adv_text_generation` | Text improvements / Advantage+ creative text generation |
| `adv_product_tags` | Add product tags |
| `adv_relevant_comments` | Relevant comments |
| `adv_enhance_cta` | Enhance CTA |
| `adv_brightness_contrast` | Adjust brightness and contrast |
| `adv_reveal_details` | Reveal details over time |
| `adv_spotlights` | Show spotlights |

### Label + ID in the same cell

For every ID column (`page_id`, `instagram_user_id`, `threads_user_id`, `existing_campaign_id`, `existing_adset_id`, `existing_post_id`, `partnership_ad_code`, `second_identity_page_id`, `second_identity_ig_id`, `pixel_id`, `application_id`, `saved_audience_id`, `video_id`, `included_custom_audience_ids`, `excluded_custom_audience_ids`), the script auto-extracts an ID in trailing parentheses. So both of these work and produce the same result:

- `445963815277238`
- `Sungboon Editor US (445963815277238)`

Useful for keeping the human-readable Page / IG / audience name next to the ID so you can verify at a glance which row uses which entity. For comma-separated columns the same rule applies per item: `"Audience X (2222),Audience Y (3333)"` is split, each item's parenthesized ID is extracted, and the result becomes `2222,3333`.

### Finding your Saved Audience ID

In Ads Manager → **Audiences**, click a saved audience. The URL contains
`...?audience_id=23851234567890123` — that number is the ID to paste into
the `saved_audience_id` column.

## Safety

- Every campaign, ad set, and ad is created with `status=PAUSED`.
- Use `--dry-run` (or the Dry-run checkbox in the web UI) first to inspect the exact payloads.
- **Rollback on failure**: if any step fails partway through a real upload, the script deletes the campaign / ad sets / ads **it created in that run** so you don't get orphan entities in Ads Manager.
- The script never modifies or deletes entities it didn't create. Pre-existing campaigns / ad sets you referenced via `existing_campaign_id` / `existing_adset_id` are explicitly protected from the rollback path — even if the upload fails mid-flight, only the new entities created during this run are removed.

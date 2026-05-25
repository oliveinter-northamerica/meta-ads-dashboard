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
| `existing_campaign_id` | optional | If set, skip campaign creation and attach new ad sets under this existing campaign. All other campaign columns on the row are ignored. Get the ID from the Ads Manager URL or Business Suite. |
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
| `existing_adset_id` | optional | If set, skip ad set creation and attach new ads under this existing ad set. All other ad-set columns on the row are ignored. |
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
| `instagram_user_id` | optional | Instagram Business Account ID to also run the ad from. Blank = Facebook only. Not the same as the Page ID — fetch via `GET <page_id>?fields=instagram_business_account` in the Graph Explorer. |
| `threads_user_id` | optional | Threads profile ID to also run the ad from. |
| `ad_name` | yes | Unique within an ad set |
| `existing_post_id` | optional | Promote an existing post from **your own Page** instead of creating a new creative. Paste the numeric Post ID (script combines with this row's `page_id`), or the full `PAGE_ID_POST_ID` form. Mutually exclusive with `partnership_ad_code`. The post supplies the image/video/body text — `image_url`, `video_id`, `primary_text`, `headline`, `description`, `display_link`, `browser_addon`, `phone_number` on this row are ignored. **But `link_url` and `cta` still apply** — they override the post's destination URL and call-to-action button on the rendered ad. |
| `partnership_ad_code` | optional | Run a post from a **partner Page** (Branded Content / Partnership Ad) using the ad code they shared with you. Must be the **full `PARTNER_PAGE_ID_POST_ID`** form (with the underscore). Same content/link/cta rules as `existing_post_id`. Your `page_id` on the row is automatically used as the sponsor identity unless overridden by the columns below. |
| `second_identity_page_id` | optional | Only used with `partnership_ad_code`. The Facebook Page that appears as the **Second identity** in Ads Manager (your brand, the paid partner). Defaults to the row's `page_id` if blank. |
| `second_identity_ig_id` | optional | Only used with `partnership_ad_code`. The Instagram profile that appears as the Second identity's IG handle. Defaults to the row's `instagram_user_id` if blank. |
| `identity_display` | optional | Only used with `partnership_ad_code`. Dropdown: blank / `DYNAMIC` (Meta picks the header that performs best — recommended), `BOTH` (both identities in the header), `FIRST_ONLY` (only the creator's identity in the header). |
| `image_url` | image OR video | Publicly fetchable image URL. **Google Drive links** in any of the standard formats (`drive.google.com/file/d/<ID>/view`, `?id=<ID>`, etc.) are auto-converted to the `lh3.googleusercontent.com/d/<ID>` form that Meta can actually fetch. Used as the video thumbnail when `video_id` is also set. |
| `video_id` | image OR video | Meta video ID for a video ad. Use this if you already uploaded the video to your ad account's media library. When set, the ad becomes a video ad instead of a static image ad. |
| `video_url` | image OR video | Alternative to `video_id` — paste any public video URL (Drive links auto-converted, same as `image_url`). The script uploads it to `/act_<id>/advideos` and uses the resulting video_id. Mutually exclusive with `video_id`. |
| `primary_text` | yes | Body copy above the ad. **Multiple variants:** separate with `\|` (e.g. `Buy now!\|Limited time!`) and the script switches the creative to `asset_feed_spec` so Meta can A/B test them. |
| `headline` | yes | Headline below the image / video title. Same `\|`-separation rule for variants. |
| `description` | yes (image ads) | Link description (small grey text under the headline). Same `\|`-separation rule for variants. Ignored for video ads. |
| `link_url` | yes | Landing page URL |
| `display_link` | optional | The URL displayed on the ad (cleaner than `link_url`, e.g. `example.com` while `link_url` is a long tracking URL). |
| `url_tags` | optional | UTM query params, e.g. `utm_source=facebook&utm_medium=cpc&utm_campaign=spring`. Auto-appended to clicks. |
| `cta` | yes | Dropdown: `SHOP_NOW`, `LEARN_MORE`, `SIGN_UP`, `SUBSCRIBE`, `DOWNLOAD`, `BOOK_TRAVEL`, `CONTACT_US`, `GET_OFFER`, `GET_QUOTE`, `APPLY_NOW`, `ORDER_NOW`, `DONATE_NOW`, `INSTALL_APP`, `USE_APP`, `WATCH_MORE`, `LISTEN_NOW`, `SEND_MESSAGE`, `MESSAGE_PAGE`, `GET_DIRECTIONS`, `CALL_NOW`, `NO_BUTTON`. Overridden by `browser_addon` when that is set to anything other than blank/`NONE`. |
| `browser_addon` | optional | Dropdown: blank or `NONE` (use `cta` as-is — this is what you want for a normal Website ad). **Warning**: setting `CALL` / `MESSENGER` / `WHATSAPP` does NOT add a button overlay on a Website ad — it **replaces the entire destination**, turning the ad into a click-to-call / click-to-Messenger / click-to-WhatsApp ad. The website URL and the chosen `cta` are both overridden. The "Browser add-on" button overlay you may have seen in Ads Manager is a UI-only feature and isn't exposed via the Marketing API; if you want that, leave this column blank and toggle it manually in Ads Manager after upload. `CALL` and `WHATSAPP` also require `phone_number`. |
| `phone_number` | conditional | Required when `browser_addon` is `CALL` or `WHATSAPP`. For WhatsApp use international format without `+` (e.g. `15551234567`). |
| `conversion_domain` | optional | The domain conversions are attributed to (e.g. `example.com`). Recommended for `OUTCOME_SALES`. |
| `advantage_plus_creative` | optional | **Master switch** for Advantage+ creative. Dropdown: blank (Meta's account default), `ON`, `OFF`. Sets a baseline for `IG_VIDEO_NATIVE_SUBTITLE`, `IMAGE_ANIMATION`, and `TEXT_OVERLAY_TRANSLATION`. The per-feature columns below override this baseline for specific features. |

**Per-feature columns**: dropdown is blank (don't touch) / `ON` / `OFF`. The Ads Manager UI label is shown alongside each. Items marked **\*** are best-guess API key names (the UI label is documented but the API key isn't) — Meta will return a clear `must be one of {...}` error if the guess is wrong, at which point tell me which one and I'll adjust.

Advantage+ creative enhancements (typically opt-in):
| Column | API key | UI label |
| --- | --- | --- |
| `adv_add_overlays` | `ADD_TEXT_OVERLAY` \* | Add overlays |
| `adv_image_touchups` | `IMAGE_TOUCHUPS` | Visual touch-ups |
| `adv_music` | `MUSIC` | Add music |
| `adv_text_generation` | `TEXT_GENERATION` | Text improvements / Advantage+ creative text generation |
| `adv_image_animation` | `IMAGE_ANIMATION` | Add animation |
| `adv_product_tags` | `PRODUCT_TAGS` \* | Add product tags (requires a connected product catalog) |

Essential enhancements (mostly on by default in Ads Manager):
| Column | API key | UI label |
| --- | --- | --- |
| `adv_relevant_comments` | `RELEVANT_COMMENTS` | Relevant comments |
| `adv_enhance_cta` | `CTA_ENHANCEMENT` | Enhance CTA |
| `adv_brightness_contrast` | `IMAGE_BRIGHTNESS_AND_CONTRAST` | Adjust brightness and contrast |
| `adv_reveal_details` | `SHOWCASE_DESTINATION` \* | Reveal details over time (destination screenshot) |
| `adv_spotlights` | `CREATIVE_HIGHLIGHTING` \* | Show spotlights (website highlights) |

Other / video / translation:
| Column | API key | UI label |
| --- | --- | --- |
| `adv_text_overlay_translation` | `TEXT_OVERLAY_TRANSLATION` | Translate text overlays |
| `adv_ig_video_subtitle` | `IG_VIDEO_NATIVE_SUBTITLE` | IG auto-subtitles (video only) |
| `adv_profile_card` | `PROFILE_CARD` | Profile card |

**Note on Advantage+ creative**: Meta's valid feature set varies by ad type, account, and what's enabled in Business Manager. Catalog-only features (`PRODUCT_TAGS`, `PRODUCT_BROWSING`, `STANDARD_ENHANCEMENTS_CATALOG`, etc.) only work on ads with a connected product catalog. If a column errors, paste the `must be one of {...}` message and we'll trim or rename.

### Finding your Saved Audience ID

In Ads Manager → **Audiences**, click a saved audience. The URL contains
`...?audience_id=23851234567890123` — that number is the ID to paste into
the `saved_audience_id` column.

## Safety

- Every campaign, ad set, and ad is created with `status=PAUSED`.
- Use `--dry-run` (or the Dry-run checkbox in the web UI) first to inspect the exact payloads.
- **Rollback on failure**: if any step fails partway through a real upload, the script deletes the campaign / ad sets / ads **it created in that run** so you don't get orphan entities in Ads Manager.
- The script never modifies or deletes entities it didn't create. Pre-existing campaigns / ad sets you referenced via `existing_campaign_id` / `existing_adset_id` are explicitly protected from the rollback path — even if the upload fails mid-flight, only the new entities created during this run are removed.

"""Shared enum values for Meta ads CSV/Excel templates.

These mirror the Meta Marketing API enums. Keep this file the single source of
truth so the CSV header, the Excel template, and the uploader stay in sync.

Required vs optional is enforced in bulk_upload.py — this file just declares
the columns and their dropdown values.
"""

CAMPAIGN_OBJECTIVES = [
    "OUTCOME_AWARENESS",
    "OUTCOME_TRAFFIC",
    "OUTCOME_ENGAGEMENT",
    "OUTCOME_LEADS",
    "OUTCOME_APP_PROMOTION",
    "OUTCOME_SALES",
]

SPECIAL_AD_CATEGORIES = [
    "NONE",
    "HOUSING",
    "CREDIT",
    "EMPLOYMENT",
    "ISSUES_ELECTIONS_POLITICS",
    "ONLINE_GAMBLING_AND_GAMING",
    "FINANCIAL_PRODUCTS_SERVICES",
]

BUYING_TYPES = ["AUCTION", "RESERVED"]

BID_STRATEGIES = [
    "LOWEST_COST_WITHOUT_CAP",
    "LOWEST_COST_WITH_BID_CAP",
    "COST_CAP",
    "LOWEST_COST_WITH_MIN_ROAS",
]

BILLING_EVENTS = [
    "IMPRESSIONS",
    "LINK_CLICKS",
    "POST_ENGAGEMENT",
    "VIDEO_VIEWS",
    "THRUPLAY",
]

OPTIMIZATION_GOALS = [
    "REACH",
    "IMPRESSIONS",
    "LINK_CLICKS",
    "LANDING_PAGE_VIEWS",
    "POST_ENGAGEMENT",
    "PAGE_LIKES",
    "VIDEO_VIEWS",
    "THRUPLAY",
    "OFFSITE_CONVERSIONS",
    "VALUE",
    "LEAD_GENERATION",
    "QUALITY_LEAD",
    "CONVERSATIONS",
    "APP_INSTALLS",
    "AD_RECALL_LIFT",
]

DESTINATION_TYPES = [
    "WEBSITE",
    "APP",
    "MESSENGER",
    "INSTAGRAM_DIRECT",
    "WHATSAPP",
    "FACEBOOK",
    "ON_AD",
    "ON_POST",
    "ON_PAGE",
    "ON_EVENT",
    "ON_VIDEO",
    "SHOP_AUTOMATIC",
]

CUSTOM_EVENT_TYPES = [
    "",
    "PURCHASE",
    "LEAD",
    "COMPLETE_REGISTRATION",
    "ADD_TO_CART",
    "INITIATE_CHECKOUT",
    "ADD_PAYMENT_INFO",
    "VIEW_CONTENT",
    "SEARCH",
    "SUBSCRIBE",
    "CONTACT",
    "DONATE",
    "OTHER",
]

PACING_TYPES = ["", "standard", "no_pacing"]

# Meta gender codes: 1 = male, 2 = female. Blank = all.
GENDERS = ["", "1", "2", "1,2"]

# "Browser add-on" overlay on website ads. When set, overrides the cta column.
# CALL and WHATSAPP also require phone_number to be filled.
BROWSER_ADDONS = ["", "NONE", "CALL", "MESSENGER", "WHATSAPP"]

# Partnership Ad — which identity (or both) shows in the ad's header.
# Mirrors Ads Manager's "Identities to display in the header" radio.
IDENTITY_DISPLAY = ["", "DYNAMIC", "BOTH", "FIRST_ONLY"]

# Master switch for Meta's Advantage+ creative enhancements. ON / OFF /
# blank (leave at Meta's account default). Script translates to
# enroll_status OPT_IN / OPT_OUT before sending to Meta.
ADVANTAGE_PLUS_CREATIVE = ["", "ON", "OFF"]

# Per-feature enrollment for Advantage+ creative. Blank = inherit master
# switch (or Meta's default), ON = OPT_IN, OFF = OPT_OUT.
ENROLL_STATUS = ["", "ON", "OFF"]

# Maps each adv_* template column to the uppercase API feature key. The
# template keeps a column for every toggle visible in Ads Manager's
# "Advantage+ creative" section so the spreadsheet matches what users
# see in the UI. At upload time the script forwards only the keys
# listed in ADVANTAGE_FEATURE_API_SUPPORTED below — the rest are
# UI-only and silently skipped (with a one-line note) because Meta
# hasn't exposed them in the Marketing API.
ADVANTAGE_FEATURE_COLUMNS = [
    # Advantage+ creative enhancements
    ("adv_add_overlays", "ADD_TEXT_OVERLAY"),
    ("adv_image_touchups", "IMAGE_TOUCHUPS"),
    ("adv_music", "MUSIC"),
    ("adv_text_generation", "TEXT_GENERATION"),
    ("adv_image_animation", "IMAGE_ANIMATION"),
    ("adv_product_tags", "PRODUCT_TAGS"),
    # Essential enhancements (mostly on by default)
    ("adv_relevant_comments", "RELEVANT_COMMENTS"),
    ("adv_enhance_cta", "CTA_ENHANCEMENT"),
    ("adv_brightness_contrast", "IMAGE_BRIGHTNESS_AND_CONTRAST"),
    ("adv_reveal_details", "SHOWCASE_DESTINATION"),
    ("adv_spotlights", "CREATIVE_HIGHLIGHTING"),
    # Other / video / translation / catalog
    ("adv_text_overlay_translation", "TEXT_OVERLAY_TRANSLATION"),
    ("adv_ig_video_subtitle", "IG_VIDEO_NATIVE_SUBTITLE"),
    ("adv_profile_card", "PROFILE_CARD"),
    ("adv_product_browsing", "PRODUCT_BROWSING"),
    ("adv_product_metadata", "PRODUCT_METADATA_AUTOMATION"),
    ("adv_catalog_enhancements", "STANDARD_ENHANCEMENTS_CATALOG"),
]

# Subset of feature keys the Marketing API currently accepts in
# degrees_of_freedom_spec.creative_features_spec. Keys not in this set
# are skipped at upload time even if the user set the column.
ADVANTAGE_FEATURE_API_SUPPORTED = {
    "IG_VIDEO_NATIVE_SUBTITLE",
    "IMAGE_ANIMATION",
    "PROFILE_CARD",
    "TEXT_OVERLAY_TRANSLATION",
    "PRODUCT_BROWSING",
    "PRODUCT_METADATA_AUTOMATION",
    "STANDARD_ENHANCEMENTS_CATALOG",
}

CTAS = [
    "SHOP_NOW",
    "LEARN_MORE",
    "SIGN_UP",
    "SUBSCRIBE",
    "DOWNLOAD",
    "BOOK_TRAVEL",
    "CONTACT_US",
    "GET_OFFER",
    "GET_QUOTE",
    "APPLY_NOW",
    "ORDER_NOW",
    "DONATE_NOW",
    "INSTALL_APP",
    "USE_APP",
    "WATCH_MORE",
    "LISTEN_NOW",
    "SEND_MESSAGE",
    "MESSAGE_PAGE",
    "GET_DIRECTIONS",
    "CALL_NOW",
    "NO_BUTTON",
]

# Columns whose cell value may carry a human-readable label before the
# actual ID, e.g. "Page ABC (123456789)" — the script extracts the value
# inside the trailing parentheses before using it.
ID_COLUMNS = {
    "existing_campaign_id",
    "existing_adset_id",
    "existing_post_id",
    "partnership_ad_code",
    "page_id",
    "instagram_user_id",
    "threads_user_id",
    "second_identity_page_id",
    "second_identity_ig_id",
    "pixel_id",
    "application_id",
    "saved_audience_id",
    "video_id",
}

# Same idea, but each cell holds a comma-separated list of IDs that the
# script splits, extracts, and rejoins.
COMMA_SEPARATED_ID_COLUMNS = {
    "included_custom_audience_ids",
    "excluded_custom_audience_ids",
}


# (column_name, dropdown_options or None)
COLUMNS = [
    # campaign
    ("existing_campaign_id", None),
    ("campaign_name", None),
    ("campaign_objective", CAMPAIGN_OBJECTIVES),
    ("buying_type", BUYING_TYPES),
    ("special_ad_categories", SPECIAL_AD_CATEGORIES),
    ("campaign_daily_budget_usd", None),
    ("campaign_lifetime_budget_usd", None),
    ("campaign_bid_strategy", BID_STRATEGIES),
    ("campaign_spend_cap_usd", None),
    ("campaign_start_time", None),
    ("campaign_stop_time", None),
    # ad set
    ("existing_adset_id", None),
    ("adset_name", None),
    ("daily_budget_usd", None),
    ("lifetime_budget_usd", None),
    ("bid_strategy", BID_STRATEGIES),
    ("bid_amount_usd", None),
    ("bid_roas_floor", None),
    ("daily_spend_cap_usd", None),
    ("lifetime_spend_cap_usd", None),
    ("pacing_type", PACING_TYPES),
    ("billing_event", BILLING_EVENTS),
    ("optimization_goal", OPTIMIZATION_GOALS),
    ("destination_type", DESTINATION_TYPES),
    ("start_time", None),
    ("end_time", None),
    ("pixel_id", None),
    ("custom_event_type", CUSTOM_EVENT_TYPES),
    ("application_id", None),
    ("object_store_url", None),
    ("dsa_beneficiary", None),
    ("dsa_payor", None),
    # targeting
    ("saved_audience_id", None),
    ("countries", None),
    ("age_min", None),
    ("age_max", None),
    ("genders", GENDERS),
    ("included_custom_audience_ids", None),
    ("excluded_custom_audience_ids", None),
    # ad / creative
    ("page_id", None),
    ("instagram_user_id", None),
    ("threads_user_id", None),
    ("ad_name", None),
    ("existing_post_id", None),
    ("partnership_ad_code", None),
    ("second_identity_page_id", None),
    ("second_identity_ig_id", None),
    ("identity_display", IDENTITY_DISPLAY),
    ("image_url", None),
    ("video_id", None),
    ("video_url", None),
    ("primary_text", None),
    ("headline", None),
    ("description", None),
    ("link_url", None),
    ("display_link", None),
    ("url_tags", None),
    ("cta", CTAS),
    ("browser_addon", BROWSER_ADDONS),
    ("phone_number", None),
    ("conversion_domain", None),
    ("advantage_plus_creative", ADVANTAGE_PLUS_CREATIVE),
] + [(col, ENROLL_STATUS) for col, _ in ADVANTAGE_FEATURE_COLUMNS]

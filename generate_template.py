"""Generate template.xlsx with data-validation dropdowns on every enum column.

Open the resulting file in Excel, Google Sheets, or Numbers — clicking an
enum cell shows a dropdown of valid Meta values.

Usage:
  python generate_template.py            # writes template.xlsx
  python generate_template.py out.xlsx
"""

import sys

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from template_options import COLUMNS

SAMPLE_ROW = {
    "campaign_name": "Spring Launch",
    "campaign_objective": "OUTCOME_TRAFFIC",
    "buying_type": "AUCTION",
    "special_ad_categories": "NONE",
    "adset_name": "US Broad 25-54",
    "daily_budget_usd": 50,
    "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
    "bid_amount_usd": "",
    "billing_event": "IMPRESSIONS",
    "optimization_goal": "LANDING_PAGE_VIEWS",
    "destination_type": "WEBSITE",
    "start_time": "",
    "end_time": "",
    "pixel_id": "",
    "custom_event_type": "",
    "saved_audience_id": "",
    "countries": "US",
    "age_min": 25,
    "age_max": 54,
    "page_id": "1234567890",
    "instagram_actor_id": "",
    "ad_name": "Ad A - Static",
    "image_url": "https://example.com/creative-a.jpg",
    "primary_text": "Discover our new spring collection.",
    "headline": "Spring is here",
    "description": "Shop the drop",
    "link_url": "https://example.com/spring",
    "url_tags": "utm_source=facebook&utm_medium=cpc&utm_campaign=spring",
    "cta": "SHOP_NOW",
}

MAX_ROWS = 500


def build(path):
    wb = Workbook()
    ws = wb.active
    ws.title = "ads"

    headers = [name for name, _ in COLUMNS]
    ws.append(headers)
    ws.append([SAMPLE_ROW.get(name, "") for name in headers])

    for col_idx, (name, options) in enumerate(COLUMNS, start=1):
        if not options:
            continue
        formula = '"' + ",".join(options) + '"'
        dv = DataValidation(type="list", formula1=formula, allow_blank=True)
        dv.error = f"Pick a valid {name}"
        dv.errorTitle = "Invalid value"
        dv.prompt = "Choose from the list"
        dv.promptTitle = name
        col_letter = get_column_letter(col_idx)
        dv.add(f"{col_letter}2:{col_letter}{MAX_ROWS}")
        ws.add_data_validation(dv)

    for col_idx, name in enumerate(headers, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = max(14, len(name) + 2)

    ws.freeze_panes = "A2"
    wb.save(path)
    print(f"Wrote {path} with {len([o for _, o in COLUMNS if o])} dropdown columns.")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "template.xlsx")

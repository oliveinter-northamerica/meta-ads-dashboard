"""Generate template.xlsx with data-validation dropdowns on every enum column.

Open the resulting file in Excel, Google Sheets, or Numbers — clicking an
enum cell shows a dropdown of valid Meta values.

Implementation: stores all dropdown option lists on an "_options" sheet
and exposes each list as a *named range* (e.g. `cta_options`). Data
validation references the name. Named ranges are the most reliable
dropdown source across Excel desktop, Excel online, Google Sheets, and
Numbers — they survive format conversions, file uploads, and edits.

Usage:
  python generate_template.py            # writes template.xlsx
  python generate_template.py out.xlsx
"""

import sys

from openpyxl import Workbook
from openpyxl.utils import get_column_letter, quote_sheetname, absolute_coordinate
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

from template_options import COLUMNS

SAMPLE_ROW = {
    "campaign_name": "My First Campaign",
    "campaign_objective": "OUTCOME_TRAFFIC",
    "buying_type": "AUCTION",
    "special_ad_categories": "NONE",
    "adset_name": "My First Ad Set",
    "daily_budget_usd": 50,
    "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
    "billing_event": "IMPRESSIONS",
    "optimization_goal": "LANDING_PAGE_VIEWS",
    "destination_type": "WEBSITE",
    "countries": "US",
    "age_min": 25,
    "age_max": 54,
    "page_id": "1234567890",
    "ad_name": "My First Ad",
    "existing_post_id": "",
    "partnership_ad_code": "",
    "image_url": "https://example.com/image.jpg",
    "primary_text": "Body copy goes here.",
    "headline": "Your headline",
    "description": "Short description.",
    "link_url": "https://example.com/landing",
    "display_link": "example.com",
    "cta": "SHOP_NOW",
    "conversion_domain": "example.com",
}

MAX_ROWS = 500


def build(path):
    wb = Workbook()
    ws = wb.active
    ws.title = "ads"

    headers = [name for name, _ in COLUMNS]
    ws.append(headers)
    ws.append([SAMPLE_ROW.get(name, "") for name in headers])

    opts_ws = wb.create_sheet("_options")
    # Visible (not hidden) so the user can confirm options are there and
    # so Google Sheets / Numbers reliably load the named ranges.

    dropdown_count = 0
    for col_idx, (name, options) in enumerate(COLUMNS, start=1):
        if not options:
            continue
        # Drop the empty-string option — allow_blank=True already permits
        # leaving cells empty, and a leading "" breaks some tools.
        values = [v for v in options if v != ""]
        if not values:
            continue

        opt_col = dropdown_count + 1
        opt_letter = get_column_letter(opt_col)

        # Header on row 1, options from row 2 onward, so the _options
        # sheet reads like a labeled reference table.
        opts_ws.cell(row=1, column=opt_col, value=name)
        for row_idx, val in enumerate(values, start=2):
            opts_ws.cell(row=row_idx, column=opt_col, value=val)

        # Define a named range like `cta_options` -> _options!$A$2:$A$22
        range_ref = (
            f"{quote_sheetname('_options')}!"
            f"{absolute_coordinate(opt_letter + '2')}:"
            f"{absolute_coordinate(opt_letter + str(len(values) + 1))}"
        )
        range_name = f"{name}_options"
        wb.defined_names[range_name] = DefinedName(
            name=range_name, attr_text=range_ref
        )

        dv = DataValidation(type="list", formula1=range_name, allow_blank=True)
        dv.error = f"Pick a valid {name}"
        dv.errorTitle = "Invalid value"
        dv.prompt = "Choose from the list"
        dv.promptTitle = name
        col_letter = get_column_letter(col_idx)
        dv.add(f"{col_letter}2:{col_letter}{MAX_ROWS}")
        ws.add_data_validation(dv)
        dropdown_count += 1

    for col_idx, name in enumerate(headers, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = max(14, len(name) + 2)

    ws.freeze_panes = "A2"
    wb.save(path)
    print(f"Wrote {path} with {dropdown_count} dropdown columns (named ranges on _options sheet).")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "template.xlsx")

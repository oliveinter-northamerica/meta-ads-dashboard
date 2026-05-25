"""Flask UI for the Meta bulk ad uploader.

Run:
  pip install -r requirements.txt
  python app.py

In a Codespace it binds to 0.0.0.0:5000 and the "Ports" tab forwards a URL.
"""

import contextlib
import io
import os
import tempfile

from flask import Flask, render_template, request, send_file
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.api import FacebookAdsApi

from bulk_upload import group, load_rows, load_rows_from_sheet, upload
from generate_template import build as build_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template(
        "index.html",
        default_token=os.environ.get("META_ACCESS_TOKEN", ""),
        default_account=os.environ.get("META_AD_ACCOUNT_ID", ""),
    )


@app.route("/template.xlsx")
def download_template():
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    tmp.close()
    build_template(tmp.name)
    return send_file(tmp.name, as_attachment=True, download_name="meta_ads_template.xlsx")


@app.route("/upload", methods=["POST"])
def upload_route():
    token = request.form.get("token", "").strip()
    account_id = request.form.get("account_id", "").strip()
    dry_run = "dry_run" in request.form
    sheet_url = request.form.get("sheet_url", "").strip()
    f = request.files.get("file")

    if sheet_url:
        try:
            rows = load_rows_from_sheet(sheet_url)
        except SystemExit as exc:
            return render_template("result.html", error=str(exc))
    elif f and f.filename:
        suffix = ".xlsx" if f.filename.lower().endswith(".xlsx") else ".csv"
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        f.save(tmp.name)
        tmp.close()
        try:
            rows = load_rows(tmp.name)
        except SystemExit as exc:
            return render_template("result.html", error=str(exc))
        finally:
            os.unlink(tmp.name)
    else:
        return render_template("result.html", error="Provide either a Google Sheets URL or a CSV/XLSX file.")

    if not dry_run and (not token or not account_id):
        return render_template("result.html", error="Token and ad account ID are required for a live upload.")

    tree, cm, am = group(rows)

    account = None
    if not dry_run:
        FacebookAdsApi.init(access_token=token)
        account = AdAccount(account_id)

    buf = io.StringIO()
    error = None
    results = []
    try:
        with contextlib.redirect_stdout(buf):
            results = upload(account, tree, cm, am, dry_run)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"

    return render_template(
        "result.html",
        results=results,
        log=buf.getvalue(),
        dry_run=dry_run,
        error=error,
        row_count=len(rows),
        account_id=account_id,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

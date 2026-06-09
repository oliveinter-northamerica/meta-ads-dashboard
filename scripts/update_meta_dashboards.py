#!/usr/bin/env python3
"""
Meta Ads Dashboard Auto-Updater
매주 모든 암호화된 Meta Ads 대시보드 페이지를 자동 업데이트합니다.

Required env vars:
  META_TOKEN          : Meta Ads API 장기 액세스 토큰
  GH_TOKEN            : GitHub PAT (contents:write)
  STATICRYPT_PASSWORD : StatiCrypt 암호화 비밀번호

Optional env vars:
  BELLA_ACCOUNT_ID    : Bella 광고 계정 ID (예: act_XXXXX7831)
                        미설정 시 /me/adaccounts에서 자동 검색
  SHEETS_ID           : Google Sheets ID (Amazon 실매출 데이터)
                        Default: 1Hko2pyCvZ3mB-ISx0Y4sGZHK0-dX37QQcqUvcGWEgCI
  DAYS                : 데이터 기간(일), default: 30
"""

from __future__ import annotations

import hashlib
import hmac as hmac_module
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# ─── Configuration ────────────────────────────────────────────────────────────
MAIN_ACCOUNT   = "act_1354817955224233"
REPO           = "oliveinter-northamerica/meta-ads-dashboard"
GRAPH_BASE     = "https://graph.facebook.com/v19.0"
GITHUB_API     = "https://api.github.com"
DEFAULT_SHEETS = "1Hko2pyCvZ3mB-ISx0Y4sGZHK0-dX37QQcqUvcGWEgCI"

KST = timezone(timedelta(hours=9))

# ─── StatiCrypt v3 Crypto (AES-CBC + PBKDF2) ──────────────────────────────────

def _pbkdf2_hex(password_str: str, salt_str: str, iterations: int, hash_name: str) -> str:
    """PBKDF2 where both password and salt are treated as UTF-8 strings."""
    dk = hashlib.pbkdf2_hmac(
        hash_name,
        password_str.encode("utf-8"),
        salt_str.encode("utf-8"),
        iterations,
        dklen=32,
    )
    return dk.hex()

def _hash_password(password: str, salt: str) -> str:
    """StatiCrypt v3 multi-round password hashing (matches JS implementation)."""
    print("  [crypto] Round 1 (PBKDF2-SHA1, 1k)…", flush=True)
    h1 = _pbkdf2_hex(password, salt, 1_000, "sha1")
    print("  [crypto] Round 2 (PBKDF2-SHA256, 14k)…", flush=True)
    h2 = _pbkdf2_hex(h1, salt, 14_000, "sha256")
    print("  [crypto] Round 3 (PBKDF2-SHA256, 585k)…", flush=True)
    h3 = _pbkdf2_hex(h2, salt, 585_000, "sha256")
    return h3

def _sign_message(hashed_password_hex: str, message_str: str) -> str:
    key = bytes.fromhex(hashed_password_hex)
    msg = message_str.encode("utf-8")
    return hmac_module.new(key, msg, "sha256").hexdigest()

def staticrypt_decrypt(html: str, password: str) -> str:
    """Decrypt a StatiCrypt v3 encrypted HTML page."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding

    salt_m = re.search(r'"staticryptSaltUniqueVariableName"\s*:\s*"([0-9a-f]+)"', html)
    enc_m  = re.search(r'"staticryptEncryptedMsgUniqueVariableName"\s*:\s*"([0-9a-f]+)"', html)
    if not salt_m or not enc_m:
        raise ValueError("Could not find staticrypt config in HTML")

    salt       = salt_m.group(1)
    signed_msg = enc_m.group(1)
    hashed     = _hash_password(password, salt)

    hmac_stored   = signed_msg[:64]
    iv_and_cipher = signed_msg[64:]
    hmac_computed = _sign_message(hashed, iv_and_cipher)
    if hmac_computed != hmac_stored:
        raise ValueError("Bad password or corrupted data (HMAC mismatch)")

    iv         = bytes.fromhex(iv_and_cipher[:32])
    ciphertext = bytes.fromhex(iv_and_cipher[32:])
    key        = bytes.fromhex(hashed)

    cipher    = Cipher(algorithms.AES(key), modes.CBC(iv))
    padded    = cipher.decryptor().update(ciphertext) + cipher.decryptor().finalize()

    # Re-create decryptor for proper finalization
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded    = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    plain    = unpadder.update(padded) + unpadder.finalize()
    return plain.decode("utf-8")

def staticrypt_encrypt(template_html: str, plaintext: str, password: str) -> str:
    """Re-encrypt plaintext, returning updated HTML with new staticryptConfig."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding

    salt   = os.urandom(16).hex()
    hashed = _hash_password(password, salt)

    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()

    iv        = os.urandom(16)
    key       = bytes.fromhex(hashed)
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    iv_and_cipher = iv.hex() + ciphertext.hex()
    signed_msg    = _sign_message(hashed, iv_and_cipher) + iv_and_cipher

    new_cfg = json.dumps({
        "staticryptEncryptedMsgUniqueVariableName": signed_msg,
        "staticryptSaltUniqueVariableName": salt,
    })
    updated = re.sub(
        r'staticryptConfig\s*=\s*\{[^}]+\}',
        f'staticryptConfig = {new_cfg}',
        template_html,
        count=1,
    )
    if updated == template_html:
        raise ValueError("Could not find staticryptConfig in template HTML")
    return updated

# ─── HTTP helpers ──────────────────────────────────────────────────────────────

def _http_get(url: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def _http_get_text(url: str) -> str:
    with urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30
    ) as r:
        return r.read().decode()

def _graph(path: str, token: str, params: dict | None = None) -> dict:
    qs  = urllib.parse.urlencode({"access_token": token, **(params or {})})
    return _http_get(f"{GRAPH_BASE}/{path}?{qs}")

# ─── Meta Ads Fetchers ─────────────────────────────────────────────────────────

def get_date_range(days: int = 30) -> tuple[str, str]:
    today = datetime.now(KST).date()
    end   = today - timedelta(days=1)
    start = end   - timedelta(days=days - 1)
    return str(start), str(end)

def fetch_daily_insights(account_id: str, token: str, days: int = 30) -> list[dict]:
    date_start, date_end = get_date_range(days)
    params = {
        "fields": "date_start,spend,impressions,clicks,actions,action_values",
        "level": "account", "time_increment": "1",
        "time_range": json.dumps({"since": date_start, "until": date_end}),
        "limit": "100",
    }
    rows = []
    for r in _graph(f"{account_id}/insights", token, params).get("data", []):
        spend_val = round(float(r.get("spend", 0)))
        actions   = {a["action_type"]: int(float(a["value"])) for a in r.get("actions", [])}
        lc        = actions.get("link_click", actions.get("outbound_click", 0))
        av        = {a["action_type"]: float(a["value"]) for a in r.get("action_values", [])}
        amz_sales = round(av.get("omni_purchase", 0))
        rows.append({
            "date": r["date_start"], "spend": spend_val,
            "impressions": int(r.get("impressions", 0)),
            "link_clicks": lc,
            "amz_sales": amz_sales,
            "amz_roas": round(amz_sales / spend_val * 100, 2) if spend_val else 0,
        })
    return sorted(rows, key=lambda x: x["date"])

def fetch_campaigns(account_id: str, token: str, days: int = 30, label: str = "main") -> list[dict]:
    date_start, date_end = get_date_range(days)
    tr = json.dumps({"since": date_start, "until": date_end})
    data = _graph(f"{account_id}/campaigns", token, {
        "fields": f"id,name,status,objective,insights.time_range({tr}){{spend,impressions,clicks}}",
        "limit": "200",
    })
    camps = []
    for c in data.get("data", []):
        ins   = c.get("insights", {}).get("data", [{}])[0] if c.get("insights") else {}
        spend = round(float(ins.get("spend", 0)))
        if spend == 0: continue
        camps.append({
            "acc": label, "id": c["id"], "name": c["name"].strip(),
            "status": c.get("status", "UNKNOWN"), "objective": c.get("objective", ""),
            "spend": spend, "impressions": int(ins.get("impressions", 0)),
            "clicks": int(ins.get("clicks", 0)),
        })
    return sorted(camps, key=lambda x: -x["spend"])

def fetch_ads(account_id: str, token: str, days: int = 30, label: str = "main") -> list[dict]:
    date_start, date_end = get_date_range(days)
    tr   = json.dumps({"since": date_start, "until": date_end})
    data = _graph(f"{account_id}/ads", token, {
        "fields": f"id,name,campaign_id,status,insights.time_range({tr}){{spend,impressions,clicks}}",
        "limit": "200",
    })
    ads = []
    for a in data.get("data", []):
        ins   = a.get("insights", {}).get("data", [{}])[0] if a.get("insights") else {}
        spend = round(float(ins.get("spend", 0)))
        if spend == 0: continue
        ads.append({
            "acc": label, "id": a["id"], "name": a["name"].strip(),
            "campaign_id": a.get("campaign_id", ""),
            "status": a.get("status", "UNKNOWN"), "spend": spend,
            "impressions": int(ins.get("impressions", 0)),
            "link_clicks": int(ins.get("clicks", 0)),
        })
    return sorted(ads, key=lambda x: -x["spend"])[:100]

def fetch_placements(account_id: str, token: str, days: int = 30) -> list[dict]:
    date_start, date_end = get_date_range(days)
    data  = _graph(f"{account_id}/insights", token, {
        "fields": "publisher_platform,spend,impressions",
        "breakdowns": "publisher_platform",
        "time_range": json.dumps({"since": date_start, "until": date_end}),
        "level": "account", "limit": "50",
    })
    rows  = data.get("data", [])
    total = sum(round(float(r.get("spend", 0))) for r in rows)
    LABEL = {"facebook": "Facebook", "instagram": "Instagram", "messenger": "Messenger",
             "audience_network": "Audience Network", "threads": "Threads"}
    result = []
    for r in rows:
        sp = round(float(r.get("spend", 0)))
        result.append({
            "name": LABEL.get(r.get("publisher_platform", ""), r.get("publisher_platform", "")),
            "spend": sp, "share": round(sp / total * 100, 2) if total else 0,
        })
    return sorted(result, key=lambda x: -x["spend"])

def fetch_meta_amazon_insights(account_id: str, token: str, days: int = 30) -> dict:
    date_start, date_end = get_date_range(days)
    now_kst = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S +09:00")
    tr      = json.dumps({"since": date_start, "until": date_end})

    kpi_raw = _graph(f"{account_id}/insights", token, {
        "fields": "spend,impressions,clicks,ctr,cpc,cpm,actions,action_values",
        "level": "account", "time_range": tr,
    }).get("data", [{}])[0]
    av          = {a["action_type"]: float(a["value"]) for a in kpi_raw.get("action_values", [])}
    acts        = {a["action_type"]: int(float(a["value"])) for a in kpi_raw.get("actions", [])}
    amz_sales   = round(av.get("omni_purchase", 0))
    total_spend = round(float(kpi_raw.get("spend", 0)))

    daily_raw = _graph(f"{account_id}/insights", token, {
        "fields": "date_start,spend,impressions,clicks,ctr,cpc,cpm",
        "level": "account", "time_increment": "1",
        "time_range": tr, "limit": "100",
    }).get("data", [])

    ads_raw = _graph(f"{account_id}/insights", token, {
        "fields": "ad_id,date_start,spend,impressions,clicks,actions,action_values",
        "level": "ad", "time_increment": "1",
        "time_range": tr, "limit": "500", "sort": "spend_descending",
    }).get("data", [])

    return {
        "kpis": {
            "account": account_id, "currency": "KRW",
            "period_start": date_start, "period_end": date_end,
            "total_spend": total_spend,
            "total_impressions": int(kpi_raw.get("impressions", 0)),
            "total_clicks": int(kpi_raw.get("clicks", 0)),
            "avg_ctr": float(kpi_raw.get("ctr", 0)),
            "avg_cpc": float(kpi_raw.get("cpc", 0)),
            "avg_cpm": float(kpi_raw.get("cpm", 0)),
            "amz_sales": amz_sales,
            "roas": round(amz_sales / total_spend, 4) if total_spend else 0,
            "amz_dpv": acts.get("landing_page_view", 0),
            "amz_atc": acts.get("add_to_cart", 0),
            "amz_purchases": acts.get("omni_purchase", 0),
            "refreshed_at": now_kst,
        },
        "daily": sorted([{
            "date": r["date_start"],
            "spend": round(float(r.get("spend", 0))),
            "impressions": int(r.get("impressions", 0)),
            "clicks": int(r.get("clicks", 0)),
            "ctr": round(float(r.get("ctr", 0)), 6),
            "cpc": round(float(r.get("cpc", 0)), 6),
            "cpm": round(float(r.get("cpm", 0)), 6),
        } for r in daily_raw], key=lambda x: x["date"]),
        "ads_daily": [{
            "ad_id": r.get("ad_id", ""), "d": r["date_start"],
            "sp": round(float(r.get("spend", 0))),
            "im": int(r.get("impressions", 0)),
            "cl": int(r.get("clicks", 0)),
            "lpv": {a["action_type"]: int(float(a["value"])) for a in r.get("actions", [])}.get("landing_page_view", 0),
            "atc": {a["action_type"]: int(float(a["value"])) for a in r.get("actions", [])}.get("add_to_cart", 0),
            "p":   {a["action_type"]: int(float(a["value"])) for a in r.get("actions", [])}.get("omni_purchase", 0),
        } for r in ads_raw if float(r.get("spend", 0)) > 0],
    }

def discover_bella_account(token: str) -> str | None:
    try:
        for acc in _graph("me/adaccounts", token, {"fields": "id,name", "limit": "50"}).get("data", []):
            if acc["id"].endswith("7831"):
                print(f"  Auto-discovered Bella: {acc['id']} ({acc['name']})")
                return acc["id"]
    except Exception as e:
        print(f"  Warning: Could not discover Bella account: {e}")
    return None

# ─── Google Sheets ─────────────────────────────────────────────────────────────

def fetch_amazon_sales_from_sheet(sheet_id: str, sheet_name: str = "Sheet1") -> list[dict]:
    url = (f"https://docs.google.com/spreadsheets/d/{sheet_id}"
           f"/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}")
    try:
        text = _http_get_text(url)
    except Exception as e:
        print(f"  Warning: Sheet fetch failed: {e}")
        return []

    import csv, io
    rows    = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2: return []
    headers = [h.strip() for h in rows[0]]

    def find_col(kws):
        for i, h in enumerate(headers):
            if any(k.lower() in h.lower() for k in kws): return i
        return -1

    date_col        = find_col(["날짜", "date", "일자"])
    main_sales_col  = find_col(["main_매출", "main매출", "main sales", "main_sales"])
    bella_sales_col = find_col(["bella_매출", "bella매출", "bella sales", "bella_sales"])
    total_sales_col = find_col(["총매출", "total", "합계", "total_sales"])

    results = []
    for row in rows[1:]:
        if not row or not (row[0] if date_col < 0 else (row[date_col] if date_col < len(row) else "")).strip():
            continue
        try:
            raw = (row[date_col] if date_col >= 0 and date_col < len(row) else row[0]).strip()
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%Y.%m.%d"):
                try:
                    date_str = datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
                    break
                except ValueError: continue
            else: continue

            def pn(col):
                if col < 0 or col >= len(row): return 0
                v = row[col].strip().replace(",","").replace("₩","").replace("$","")
                return round(float(v)) if v else 0

            main_s  = pn(main_sales_col)
            bella_s = pn(bella_sales_col)
            results.append({
                "date": date_str, "main_sales": main_s, "bella_sales": bella_s,
                "total_sales": pn(total_sales_col) if total_sales_col >= 0 else main_s + bella_s,
            })
        except Exception: continue

    return sorted(results, key=lambda x: x["date"])

# ─── Data Builders ─────────────────────────────────────────────────────────────

def _js_arr(rows: list) -> str:
    lines = [f"  {json.dumps(r, ensure_ascii=False)}" for r in rows]
    return "[\n" + ",\n".join(lines) + "\n]"

def build_campaigns_js(main_daily, campaigns, placements, days=30) -> str:
    ds, de = get_date_range(days)
    now  = datetime.now(KST).strftime("%Y-%m-%d")
    meta = {"accountName": "[북미]성분에디터_아마존", "accountId": MAIN_ACCOUNT,
            "currency": "KRW", "generatedAt": now, "dateRange": f"{ds} – {de}"}
    camps = [{"id": c["id"], "name": c["name"], "status": c["status"].title(),
              "objective": c["objective"], "spend": c["spend"],
              "impressions": c["impressions"], "clicks": c["clicks"],
              "ctr": round(c["clicks"]/c["impressions"]*100,4) if c["impressions"] else 0,
              "cpc": round(c["spend"]/c["clicks"]) if c["clicks"] else 0}
             for c in campaigns[:50]]
    ts = [{"date": d["date"], "spend": d["spend"], "impressions": d["impressions"],
           "clicks": d["link_clicks"]} for d in main_daily]
    J  = lambda o: json.dumps(o, ensure_ascii=False, indent=2)
    return f"// Auto-generated {now}\nconst meta={J(meta)};\nconst campaigns={J(camps)};\nconst timeseries={J(ts)};\nconst placements={J(placements)};\n"

def build_meta_daily_js(main_daily, bella_daily, mc, bc, ma, ba) -> str:
    def dr(d): return [d["date"],d["spend"],d["impressions"],d["link_clicks"],d["amz_sales"],d["amz_roas"]]
    ac  = mc + bc
    ds, de = get_date_range(30)
    now = datetime.now(KST).strftime("%Y-%m-%d")
    cname = {c["id"]: c["name"] for c in ac if "id" in c}
    return "\n".join([
        f"// Auto-generated: {now} | {ds}~{de}",
        f"const MAIN={_js_arr([dr(d) for d in main_daily])};",
        f"const BELLA={_js_arr([dr(d) for d in bella_daily])};",
        "// [acc,name,status,objective,spend,impressions,clicks]",
        f"const CAMP={_js_arr([[c['acc'],c['name'],c['status'],c['objective'],c['spend'],c['impressions'],c['clicks']] for c in ac])};",
        f"const CNAME={json.dumps(cname, ensure_ascii=False)};",
        "// [acc,adName,campaignId,status,spend,impressions,linkClicks]",
        f"const ADS={_js_arr([[a['acc'],a['name'],a.get('campaign_id',''),a['status'],a['spend'],a['impressions'],a['link_clicks']] for a in ma+ba])};",
    ]) + "\n"

def build_meta_combined_js(main_daily, bella_daily, mc, bc, ma, ba) -> str:
    def mk(r):
        d = datetime.strptime(r["date"], "%Y-%m-%d")
        return {"d": d.strftime("%m-%d"), "sp": r["spend"], "im": r["impressions"], "lc": r["link_clicks"]}
    ac    = mc + bc; aa = ma + ba
    ds, de = get_date_range(30)
    now   = datetime.now(KST).strftime("%Y-%m-%d")
    camps = [{"name":c["name"],"a":"M" if c["acc"]=="main" else "B","st":c["status"],"ob":c["objective"],"sp":c["spend"],"im":c["impressions"],"lc":c["clicks"]} for c in ac]
    ads   = [{"acc":a["acc"],"name":a["name"],"cid":a.get("campaign_id",""),"st":a["status"],"sp":a["spend"],"im":a["impressions"],"lc":a["link_clicks"]} for a in aa]
    J     = lambda o: json.dumps(o, ensure_ascii=False, indent=2)
    return f"// Auto-generated: {now} | {ds}~{de}\nconst MAIN_D={J([mk(r) for r in main_daily])};\nconst BELLA_D={J([mk(r) for r in bella_daily])};\nconst CAMPS={J(camps)};\nconst ADS={J(ads)};\n"

def build_meta_amazon_js(data: dict) -> str:
    return f"// Auto-generated: {data['kpis']['refreshed_at']}\nconst DATA={json.dumps(data, ensure_ascii=False, indent=2)};\n"

def build_ads_daily_js(md, bd, amz_sales, mc, bc, ma, ba) -> str:
    def dr(d): return [d["date"],d["spend"],d["impressions"],d["link_clicks"],d["amz_sales"],d["amz_roas"]]
    ab   = {r["date"]: r for r in amz_sales}
    all_dates = sorted(set(d["date"] for d in md + bd))
    amz  = [[dt, ab.get(dt,{}).get("total_sales",0), ab.get(dt,{}).get("main_sales",0),
              ab.get(dt,{}).get("bella_sales",0),
              next((d["spend"] for d in md if d["date"]==dt),0), 0,
              next((d["spend"] for d in bd if d["date"]==dt),0)] for dt in all_dates]
    ac   = mc+bc; aa = ma+ba
    ds, de = get_date_range(30)
    now  = datetime.now(KST).strftime("%Y-%m-%d")
    cname = {c["id"]: c["name"] for c in ac if "id" in c}
    return "\n".join([
        f"// Auto-generated: {now} | {ds}~{de}",
        f"const MAIN={_js_arr([dr(d) for d in md])};",
        f"const BELLA={_js_arr([dr(d) for d in bd])};",
        "// [date,total_amz_sales,main_amz_sales,bella_amz_sales,main_spend,0,bella_spend]",
        f"const AMZ={_js_arr(amz)};",
        f"const CAMP={_js_arr([[c['acc'],c['name'],c['status'],c['objective'],c['spend'],c['impressions'],c['clicks']] for c in ac])};",
        f"const CNAME={json.dumps(cname, ensure_ascii=False)};",
        f"const ADS={_js_arr([[a['acc'],a['name'],a.get('campaign_id',''),a['status'],a['spend'],a['impressions'],a['link_clicks']] for a in aa])};",
    ]) + "\n"

# ─── HTML Patcher ──────────────────────────────────────────────────────────────

def replace_data_script(decrypted_html: str, new_data_js: str) -> str:
    """Replace the auto-generated <script>…</script> data block."""
    pattern = (
        r'(<script>)'
        r'\s*(?:// Auto-generated|const MAIN\s*=|const MAIN_D\s*=|const DATA\s*=)'
        r'.*?'
        r'(</script>)'
    )
    repl = r'\g<1>\n' + new_data_js.replace('\\', r'\\') + r'\n\g<2>'
    updated, n = re.subn(pattern, repl, decrypted_html, count=1, flags=re.DOTALL)
    if n == 0:
        raise ValueError("Data script block not found in decrypted HTML")
    return updated

# ─── GitHub Helpers ────────────────────────────────────────────────────────────

def _gh_hdrs(token: str) -> dict:
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def get_raw_file(path: str, token: str) -> tuple[str, str]:
    import base64
    data = _http_get(f"{GITHUB_API}/repos/{REPO}/contents/{path}", _gh_hdrs(token))
    return base64.b64decode(data["content"].replace("\n","")).decode("utf-8"), data["sha"]

def put_file(path: str, content: str, sha: str, token: str) -> None:
    import base64
    now  = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    body = json.dumps({
        "message": f"chore: Meta 대시보드 자동 갱신 {now}",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "sha": sha,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{GITHUB_API}/repos/{REPO}/contents/{path}", data=body, method="PUT",
        headers={**_gh_hdrs(token), "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()

# ─── Page Updater ──────────────────────────────────────────────────────────────

def update_page(path: str, new_data_js: str, password: str, gh_token: str) -> None:
    print(f"\n── {path}")
    print("  fetch…", end=" ", flush=True)
    html, sha = get_raw_file(path, gh_token)
    print("decrypt…", end=" ", flush=True)
    plain = staticrypt_decrypt(html, password)
    print("patch…", end=" ", flush=True)
    patched = replace_data_script(plain, new_data_js)
    print("encrypt…", end=" ", flush=True)
    new_html = staticrypt_encrypt(html, patched, password)
    print("push…", end=" ", flush=True)
    put_file(path, new_html, sha, gh_token)
    print("✓")

# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    meta_token = os.environ.get("META_TOKEN", "")
    gh_token   = os.environ.get("GH_TOKEN",   "")
    password   = os.environ.get("STATICRYPT_PASSWORD", "")
    bella_id   = os.environ.get("BELLA_ACCOUNT_ID", "")
    sheets_id  = os.environ.get("SHEETS_ID", DEFAULT_SHEETS)
    days       = int(os.environ.get("DAYS", "30"))

    if not all([meta_token, gh_token, password]):
        print("ERROR: META_TOKEN, GH_TOKEN, STATICRYPT_PASSWORD 필요", file=sys.stderr)
        sys.exit(1)

    if not bella_id:
        print("Bella 계정 검색 중…")
        bella_id = discover_bella_account(meta_token)
    if not bella_id:
        print("WARNING: Bella 계정 없음 — Bella 배열은 빈 배열로 처리됨")

    ds, de = get_date_range(days)
    print(f"기간: {ds} ~ {de}  ({days}일)")

    print("\n[1/6] Main 일별 인사이트…")
    md = fetch_daily_insights(MAIN_ACCOUNT, meta_token, days)
    print(f"      {len(md)}일")

    print("[2/6] Main 캠페인…")
    mc = fetch_campaigns(MAIN_ACCOUNT, meta_token, days, "main")

    print("[3/6] Main 광고…")
    ma = fetch_ads(MAIN_ACCOUNT, meta_token, days, "main")

    print("[4/6] Main 지면…")
    pl = fetch_placements(MAIN_ACCOUNT, meta_token, days)

    bd = bc = ba = []
    if bella_id:
        print("[5/6] Bella 데이터…")
        bd = fetch_daily_insights(bella_id, meta_token, days)
        bc = fetch_campaigns(bella_id, meta_token, days, "bella")
        ba = fetch_ads(bella_id, meta_token, days, "bella")
    else:
        print("[5/6] Bella 스킵")

    print("[6/6] Meta+Amazon Attribution 인사이트…")
    maz_data = fetch_meta_amazon_insights(MAIN_ACCOUNT, meta_token, days)

    print("      Google Sheets 아마존 실매출…")
    amz = fetch_amazon_sales_from_sheet(sheets_id)
    print(f"      {len(amz)}행")

    pages = {
        "campaigns.html":                       build_campaigns_js(md, mc, pl, days),
        "meta-daily.html":                      build_meta_daily_js(md, bd, mc, bc, ma, ba),
        "meta-combined.html":                   build_meta_combined_js(md, bd, mc, bc, ma, ba),
        "meta-amazon.html":                     build_meta_amazon_js(maz_data),
        "ads_daily_withAmazonSales/index.html": build_ads_daily_js(md, bd, amz, mc, bc, ma, ba),
    }

    errors = []
    for path, data_js in pages.items():
        try:
            update_page(path, data_js, password, gh_token)
        except Exception as e:
            import traceback; traceback.print_exc()
            errors.append((path, str(e)))

    if errors:
        print(f"\n{len(errors)}개 실패:", file=sys.stderr)
        for p, e in errors: print(f"  ✗ {p}: {e}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\n✓ 전체 {len(pages)}개 페이지 갱신 완료")

if __name__ == "__main__":
    main()

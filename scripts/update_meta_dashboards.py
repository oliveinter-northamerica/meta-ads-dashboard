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
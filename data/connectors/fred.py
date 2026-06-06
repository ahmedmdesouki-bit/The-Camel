"""
FRED connector (S8) — macro series observations → camel_macro.db.

Uses the FRED observations API (JSON). When ALFRED vintage fields are present (`realtime_start`),
they populate `reported_at`, giving honest point-in-time macro. Missing FRED values ('.') are skipped.
Network only via the injected transport; tests pass canned JSON.
"""
from __future__ import annotations
import os
from urllib.parse import urlencode, urlparse, parse_qs
from typing import List

from data.connectors.macro_base import MacroConnector
from data.source_registry import FRED


class FredConnector(MacroConnector):
    spec = FRED
    parser_version = "fred.v1"

    def urls(self, series_id: str, api_key: str = None, **_) -> List[str]:
        key = api_key or os.environ.get("FRED_API_KEY", "")
        q = urlencode({"series_id": series_id, "api_key": key, "file_type": "json"})
        return [f"{self.spec.base_url}/series/observations?{q}"]

    def parse(self, raw: str, url: str) -> List[dict]:
        series_id = parse_qs(urlparse(url).query).get("series_id", [""])[0]
        data = self.parse_json(raw)
        out = []
        for obs in data.get("observations", []):
            val = obs.get("value")
            if val in (None, "", "."):          # FRED missing-value marker
                continue
            try:
                value = float(val)
            except (TypeError, ValueError):      # non-numeric → skip this obs, don't abort the run
                continue
            if not obs.get("date"):
                continue
            rec = {
                "series_id": series_id, "indicator": series_id,
                "value": value, "event_date": obs.get("date"),
            }
            if obs.get("realtime_start"):       # ALFRED vintage → real reported_at
                rec["reported_at"] = obs["realtime_start"]
            out.append(rec)
        return out
    # store() inherited from MacroConnector → macro_observations

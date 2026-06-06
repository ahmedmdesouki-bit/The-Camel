"""
US Treasury Fiscal Data connector (S8) — average interest rates → camel_macro.db.

Free, no API key, clean JSON. `record_date` → event_date; `security_desc` → indicator.
"""
from __future__ import annotations
from typing import List

from data.connectors.macro_base import MacroConnector
from data.source_registry import TREASURY


class TreasuryConnector(MacroConnector):
    spec = TREASURY
    parser_version = "treasury.v1"

    def urls(self, dataset: str = "v2/accounting/od/avg_interest_rates",
             page_size: int = 100, **_) -> List[str]:
        return [f"{self.spec.base_url}/{dataset}?sort=-record_date&page[size]={page_size}"]

    def parse(self, raw: str, url: str) -> List[dict]:
        data = self.parse_json(raw)
        out = []
        for row in data.get("data", []):
            val = row.get("avg_interest_rate_amt")
            if val in (None, ""):
                continue
            desc = row.get("security_desc", "rate")
            out.append({
                "series_id": f"treasury:{desc}", "indicator": desc,
                "value": float(val), "event_date": row.get("record_date"),
            })
        return out

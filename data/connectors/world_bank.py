"""
World Bank Indicators connector (S8) — commodities / global macro → camel_macro.db.

Free, no API key. The World Bank API returns `[metadata, [observations…]]`; we read the second
element. Null values are skipped. Annual values stamp event_date as YYYY-12-31.
"""
from __future__ import annotations
from typing import List

from data.connectors.macro_base import MacroConnector
from data.source_registry import WORLD_BANK


class WorldBankConnector(MacroConnector):
    spec = WORLD_BANK
    parser_version = "world_bank.v1"

    def urls(self, indicator: str, country: str = "WLD", date_range: str = "2015:2026",
             per_page: int = 1000, **_) -> List[str]:
        return [f"{self.spec.base_url}/country/{country}/indicator/{indicator}"
                f"?format=json&date={date_range}&per_page={per_page}"]

    def parse(self, raw: str, url: str) -> List[dict]:
        data = self.parse_json(raw)
        rows = data[1] if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list) else []
        out = []
        for row in rows:
            v = row.get("value")
            if v is None:
                continue
            ind = (row.get("indicator") or {}).get("id", "")
            ctry = (row.get("country") or {}).get("id", "WLD")
            out.append({
                "series_id": f"{ind}:{ctry}", "indicator": ind, "region": ctry,
                "value": float(v), "event_date": f'{row.get("date")}-12-31',
            })
        return out

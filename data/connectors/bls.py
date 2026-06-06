"""
BLS connector (S8) — CPI / employment series → camel_macro.db.

Uses the BLS public v1 timeseries GET (no key). Period codes map to an event_date:
monthly M01–M12 → first of month; quarterly Q01–Q04 → quarter-end month; annual → YYYY-12-31.
"""
from __future__ import annotations
from typing import List

from data.connectors.macro_base import MacroConnector
from data.source_registry import BLS

_Q_END = {"Q01": "03", "Q02": "06", "Q03": "09", "Q04": "12"}


def _event_date(year: str, period: str) -> str:
    if period.startswith("M") and period[1:].isdigit():
        return f"{year}-{int(period[1:]):02d}-01"
    if period in _Q_END:
        return f"{year}-{_Q_END[period]}-01"
    return f"{year}-12-31"


class BlsConnector(MacroConnector):
    spec = BLS
    parser_version = "bls.v1"

    def urls(self, series_id: str, **_) -> List[str]:
        return [f"{self.spec.base_url}/v1/timeseries/data/{series_id}"]

    def parse(self, raw: str, url: str) -> List[dict]:
        data = self.parse_json(raw)
        out = []
        for s in ((data.get("Results") or {}).get("series") or []):
            sid = s.get("seriesID", "")
            for d in s.get("data", []):
                val = d.get("value")
                if val in (None, ""):
                    continue
                out.append({
                    "series_id": sid, "indicator": sid,
                    "value": float(val),
                    "event_date": _event_date(str(d.get("year")), d.get("period", "")),
                })
        return out

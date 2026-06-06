"""
BEA connector (S8) — GDP / income / spending → camel_macro.db.

Uses the BEA Data API (JSON). Generic: the caller passes the BEA `query` dict (datasetname,
TableName, Frequency, Year, …); we add UserID/method/format. TimePeriod → event_date.
"""
from __future__ import annotations
import os
from urllib.parse import urlencode
from typing import List

from data.connectors.macro_base import MacroConnector
from data.source_registry import BEA


def _bea_date(tp: str) -> str:
    tp = str(tp or "")
    if "Q" in tp:                                   # 2025Q1 → quarter-end
        y, q = tp.split("Q")
        return f"{y}-{['03', '06', '09', '12'][int(q) - 1]}-01"
    if "M" in tp:                                   # 2025M05 → month
        y, m = tp.split("M")
        return f"{y}-{int(m):02d}-01"
    return f"{tp}-12-31" if tp else ""              # annual


class BeaConnector(MacroConnector):
    spec = BEA
    parser_version = "bea.v1"

    def urls(self, query: dict = None, key: str = None, **_) -> List[str]:
        q = dict(query or {})
        q.setdefault("UserID", key or os.environ.get("BEA_API_KEY", ""))
        q.setdefault("method", "GetData")
        q.setdefault("ResultFormat", "JSON")
        return [f"{self.spec.base_url}/api/data?{urlencode(q)}"]

    def parse(self, raw: str, url: str) -> List[dict]:
        data = self.parse_json(raw)
        rows = (((data.get("BEAAPI") or {}).get("Results") or {}).get("Data")) or []
        out = []
        for r in rows:
            v = r.get("DataValue")
            if v in (None, ""):
                continue
            try:
                val = float(str(v).replace(",", ""))
            except ValueError:
                continue
            desc = r.get("LineDescription") or r.get("SeriesCode") or "bea"
            ed = _bea_date(r.get("TimePeriod"))
            if not ed:
                continue
            out.append({"series_id": f"bea:{desc}", "indicator": desc, "value": val,
                        "event_date": ed})
        return out

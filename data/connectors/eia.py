"""
EIA connector (S8) — energy (oil/gas/inventories) → camel_macro.db.

Uses the EIA v2 API (JSON). Generic: the caller passes a `route` (e.g. petroleum/pri/spt) and a
`query` dict of facets; we add the api_key + JSON output. `period` → event_date.
"""
from __future__ import annotations
import os
from urllib.parse import urlencode
from typing import List

from data.connectors.macro_base import MacroConnector
from data.source_registry import EIA


_Q_END = {"Q1": "03", "Q2": "06", "Q3": "09", "Q4": "12"}


def _eia_date(period: str) -> str:
    p = str(period or "")
    if len(p) == 4:                       # annual YYYY
        return f"{p}-12-31"
    if len(p) == 6 and "Q" in p:          # quarterly YYYYQn
        y, q = p.split("Q")
        return f"{y}-{_Q_END.get('Q' + q, '12')}-01"
    if len(p) == 7:                       # monthly YYYY-MM
        return f"{p}-01"
    return p                               # already a full date (YYYY-MM-DD)


class EiaConnector(MacroConnector):
    spec = EIA
    parser_version = "eia.v1"

    def urls(self, route: str, query: dict = None, key: str = None, **_) -> List[str]:
        q = dict(query or {})
        q.setdefault("api_key", key or os.environ.get("EIA_API_KEY", ""))
        q.setdefault("out", "json")
        return [f"{self.spec.base_url}/v2/{route}/data/?{urlencode(q)}"]

    def parse(self, raw: str, url: str) -> List[dict]:
        data = self.parse_json(raw)
        rows = ((data.get("response") or {}).get("data")) or []
        out = []
        for r in rows:
            v = r.get("value")
            if v in (None, ""):
                continue
            try:
                val = float(v)
            except (ValueError, TypeError):
                continue
            desc = r.get("series-description") or r.get("series") or r.get("product") or "eia"
            ed = _eia_date(r.get("period"))
            if not ed:
                continue
            out.append({"series_id": f"eia:{desc}", "indicator": desc, "value": val,
                        "event_date": ed})
        return out

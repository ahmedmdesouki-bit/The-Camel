"""
GPR connector (S8 backlog, built S17) — the Caldara-Iacoviello Geopolitical Risk Index → camel_macro.db.

Scope decision (zero-dependency): the canonical GPR file is Excel, but this connector reads **CSV** (stdlib
`csv`, no openpyxl/pandas) — the founder points it at the CSV export / mirror. It parses the month + the
headline `GPR` column into point-in-time `macro_observations` (series_id `GPR`), and the regime feature
builder + classifier then treat an ELEVATED GPR as a geopolitical-risk-off contribution. Defensive parsing:
it tolerates `1985M01` / `1985-01` / `1985-01-01` dates and a case-insensitive `GPR` column, and the base
validator drops any row it cannot date — so a format drift degrades gracefully instead of fabricating data.
"""
from __future__ import annotations

import re
from typing import List, Optional

from data.connectors.macro_base import MacroConnector
from data.source_registry import GPR


def _to_event_date(s: str) -> Optional[str]:
    """Normalize a GPR date cell to an ISO event_date (YYYY-MM-01), or None if it can't be parsed."""
    s = (s or "").strip()
    if not s:
        return None
    m = re.match(r"^(\d{4})[Mm](\d{1,2})$", s)             # 1985M01
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-01"
    parts = s.replace("/", "-").split("-")                 # 1985-01 / 1985-01-01
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        day = parts[2].zfill(2) if len(parts) >= 3 and parts[2].isdigit() else "01"
        return f"{parts[0]}-{parts[1].zfill(2)}-{day}"
    return None


class GPRConnector(MacroConnector):
    spec = GPR
    parser_version = "gpr.v1"

    def urls(self, file: str = "data_gpr_export.csv", **_) -> List[str]:
        return [f"{self.spec.base_url}/{file}"]

    def parse(self, raw: str, url: str) -> List[dict]:
        out: List[dict] = []
        for row in self.parse_csv(raw):
            low = {(k or "").strip().lower(): v for k, v in row.items()}
            ed = _to_event_date(low.get("month") or low.get("date") or low.get("observation_date") or "")
            val = low.get("gpr")
            if not ed or val in (None, ""):
                continue
            try:
                value = float(val)
            except (TypeError, ValueError):
                continue
            out.append({"series_id": "GPR", "indicator": "geopolitical_risk_index",
                        "region": "GLOBAL", "value": value, "event_date": ed})
        return out

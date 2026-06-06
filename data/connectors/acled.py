"""
ACLED connector (S8) — armed conflict / protest events → camel_news.db.

ACLED read API (JSON). Each event becomes a STRUCTURED news event whose title is built only from
safe structured fields (event_type + country) — the free-text `notes` are NOT stored, so no hostile
text enters the pipeline. Inherits NewsConnector's sanitise/redact discipline.
"""
from __future__ import annotations
import os
from urllib.parse import urlencode
from typing import List

from data.connectors.news_base import NewsConnector
from data.source_registry import ACLED


class AcledConnector(NewsConnector):
    spec = ACLED
    parser_version = "acled.v1"

    def urls(self, country: str = None, key: str = None, email: str = None,
             limit: int = 50, **_) -> List[str]:
        q = {"key": key or os.environ.get("ACLED_API_KEY", ""),
             "email": email or os.environ.get("ACLED_EMAIL", ""),
             "limit": limit}
        if country:
            q["country"] = country
        return [f"{self.spec.base_url}/acled/read?{urlencode(q)}"]

    def parse(self, raw: str, url: str) -> List[dict]:
        data = self.parse_json(raw)
        out = []
        for e in data.get("data", []):
            ed = e.get("event_date")
            if not ed:
                continue
            etype = e.get("event_type", "event")
            country = e.get("country", "")
            did = e.get("data_id") or e.get("event_id_cnty") or ed
            out.append(self.make_event(
                title=f"{etype} in {country}",          # structured fields only — never the notes
                url=f"https://acleddata.com/event/{did}",
                event_date=ed, event_type="conflict_event", source_country=country,
            ))
        return out

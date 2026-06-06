"""
GDELT connector (S8) — global news as STRUCTURED events → camel_news.db.

Uses the GDELT DOC 2.0 ArtList API (JSON). Each article becomes a structured event with a SANITISED
title (redacted if injection-flagged — see NewsConnector). Articles missing a url or seendate are
skipped. Raw article bodies are never fetched or stored.
"""
from __future__ import annotations
from urllib.parse import urlencode
from typing import List

from data.connectors.news_base import NewsConnector
from data.source_registry import GDELT


class GdeltConnector(NewsConnector):
    spec = GDELT
    parser_version = "gdelt.v1"

    def urls(self, query: str, maxrecords: int = 75, **_) -> List[str]:
        q = urlencode({"query": query, "mode": "ArtList", "format": "json",
                       "maxrecords": maxrecords})
        return [f"{self.spec.base_url}/api/v2/doc/doc?{q}"]

    def parse(self, raw: str, url: str) -> List[dict]:
        data = self.parse_json(raw)
        out = []
        for a in data.get("articles", []):
            u, seen = a.get("url"), a.get("seendate")
            if not u or not seen or len(seen) < 8:
                continue                                  # malformed → skip
            event_date = f"{seen[0:4]}-{seen[4:6]}-{seen[6:8]}"
            out.append(self.make_event(
                title=a.get("title"), url=u, event_date=event_date,
                domain=a.get("domain"), language=a.get("language"),
                source_country=a.get("sourcecountry"),
            ))
        return out

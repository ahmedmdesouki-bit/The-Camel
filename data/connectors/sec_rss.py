"""
SEC EDGAR filings-RSS connector (S8 completion) — 8-K filing *events* → camel_news.db `news_events`.

SEC publishes recent filings as an Atom feed (no API key). 8-K = "material event" disclosures, so this is
a free, official, point-in-time event stream that feeds the S9 event-intelligence / event_reactions study.
Subclasses NewsConnector, so every filing title runs through the injection sanitiser and only structured
fields are stored (no raw body). Atom parsed with stdlib xml.etree (no feedparser dependency). Network only
through the injected transport — tests pass canned Atom XML.
"""
from __future__ import annotations
import xml.etree.ElementTree as ET
from typing import List

from data.connectors.news_base import NewsConnector
from data.source_registry import SEC_RSS


def _localname(tag: str) -> str:
    """Strip the XML namespace: '{http://www.w3.org/2005/Atom}entry' -> 'entry'."""
    return tag.rsplit("}", 1)[-1]


class SecRssConnector(NewsConnector):
    spec = SEC_RSS
    parser_version = "sec_rss.v1"
    # SEC's fair-access policy requires a descriptive, contactable UA (set by the founder before live).
    headers = {"User-Agent": "TheCamel/0.1 (personal research; contact: founder@thecamel.local)",
               "Accept-Encoding": "identity"}

    def urls(self, feed_url: str = "", cik: str = "", filing_type: str = "8-K", count: int = 40, **_) -> List[str]:
        if feed_url:
            return [feed_url]
        base = f"{self.spec.base_url}/cgi-bin/browse-edgar?action=getcompany&output=atom&type={filing_type}&count={count}"
        if cik:
            base += f"&CIK={cik}"
        return [base]

    def parse(self, raw: str, url: str) -> List[dict]:
        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            return []                                   # malformed feed → nothing (fail-safe), don't abort
        out: List[dict] = []
        for el in root.iter():
            if _localname(el.tag) != "entry":
                continue
            title = link = updated = category = ""
            for child in el:
                name = _localname(child.tag)
                if name == "title":
                    title = (child.text or "").strip()
                elif name == "updated" and child.text:
                    updated = child.text.strip()[:10]   # YYYY-MM-DD
                elif name == "link":
                    link = child.get("href", "") or link
                elif name == "category":
                    category = child.get("term", "") or category
            if not title or not updated:
                continue                                 # an entry with no title/date isn't point-in-time honest
            out.append(self.make_event(
                title=title, url=link or url, event_date=updated,
                event_type="sec_filing", direction=None,
            ))
        return out

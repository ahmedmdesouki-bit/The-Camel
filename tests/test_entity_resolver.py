"""
S9 slice 1 — entity resolution: a ticker → full cross-graph identity.

Seeded realistically via the S8 connectors (SEC EDGAR + ETF holdings) plus the whitelist, then
resolved. Proves the S9 gate's identity half: identity + CIK + sector + Sharia status + ETF
look-through exposure + latest filing for a given ticker.
"""
from data.entity_resolver import resolve, register_asset, etf_exposure
from sharia.whitelist import add_instrument, freeze_instrument
from data.connectors.sec_edgar import SecEdgarConnector
from data.connectors.etf_holdings import EtfHoldingsConnector

NOW = "2026-06-06T00:00:00+00:00"

SEC_JSON = """
{"cik": 320193, "taxonomy": "us-gaap", "tag": "Revenues", "units": {"USD": [
  {"end": "2025-09-30", "val": 391035000000, "fy": 2025, "fp": "FY", "form": "10-K",
   "filed": "2025-11-01", "accn": "0000320193-25-000001"}
]}}
"""

SPUS_CSV = """Ticker,Name,Weight (%),Shares
AAPL,Apple Inc,8.50,1000
MSFT,Microsoft Corp,7.20,800
"""


def _seed(dbs):
    register_asset(dbs, "AAPL", cik="0000320193", name="Apple Inc", sector="Technology")
    add_instrument(dbs.sharia, "AAPL", "equity", approved_by="chiko", scan_id="s1",
                   sharia_status="compliant")
    SecEdgarConnector().run(dbs.fundamentals, transport=lambda u: SEC_JSON,
                            cik=320193, concept="Revenues", symbol="AAPL", now=NOW)
    EtfHoldingsConnector().run(dbs.sharia, transport=lambda u: SPUS_CSV,
                               holdings_url="https://issuer.example/SPUS.csv", etf="SPUS",
                               as_of="2026-05-31", now=NOW)


def test_resolve_full_identity(dbs):
    _seed(dbs)
    r = resolve(dbs, "aapl")                       # case-insensitive
    assert r.symbol == "AAPL" and r.cik == "0000320193"
    assert r.name == "Apple Inc" and r.sector == "Technology"
    assert r.sharia_status == "compliant" and r.on_whitelist and not r.frozen
    assert any(e["etf"] == "SPUS" for e in r.etf_exposure)
    assert r.latest_filing and r.latest_filing["concept"] == "Revenues"
    assert r.benchmark == "SPUS" and r.known


def test_resolve_reflects_freeze(dbs):
    _seed(dbs)
    freeze_instrument(dbs.sharia, "AAPL", reason="drift")
    assert resolve(dbs, "AAPL").frozen is True


def test_resolve_unknown_ticker_is_empty_but_safe(dbs):
    r = resolve(dbs, "ZZZZ")
    assert not r.on_whitelist and r.sharia_status == "unknown"
    assert r.etf_exposure == [] and r.latest_filing is None and not r.known


def test_etf_exposure_reverse_lookup(dbs):
    _seed(dbs)
    etfs = {e["etf"] for e in etf_exposure(dbs, "AAPL")}
    assert "SPUS" in etfs
    assert {e["etf"] for e in etf_exposure(dbs, "MSFT")} == {"SPUS"}


def test_delisted_flag_surfaced(dbs):
    register_asset(dbs, "OLDCO", name="Old Co", sector="Energy", delisted=True)
    assert resolve(dbs, "OLDCO").delisted is True


def test_register_asset_upsert_coalesces(dbs):
    register_asset(dbs, "AAPL", cik="0000320193", name="Apple Inc", sector="Tech")
    register_asset(dbs, "AAPL", sector="Technology")          # partial update must not wipe name/cik
    r = resolve(dbs, "AAPL")
    assert r.name == "Apple Inc" and r.cik == "0000320193" and r.sector == "Technology"

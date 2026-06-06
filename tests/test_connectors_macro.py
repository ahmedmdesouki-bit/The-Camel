"""
S8 slice 2 — three more macro connectors (Treasury, World Bank, BLS) → macro_observations.
Hermetic: canned payloads via the injected transport.
"""
import sqlite3
import pytest

from data.source_registry import all_specs
from data.connectors.treasury import TreasuryConnector
from data.connectors.world_bank import WorldBankConnector
from data.connectors.bls import BlsConnector

NOW = "2026-06-06T00:00:00+00:00"


def _stub(payload: str):
    return lambda url: payload


def _count(db, where=""):
    with sqlite3.connect(db) as c:
        return c.execute(f"SELECT COUNT(*) FROM macro_observations {where}").fetchone()[0]


TREASURY_JSON = """
{"data": [
  {"record_date": "2026-05-31", "security_desc": "Treasury Notes", "avg_interest_rate_amt": "2.85"},
  {"record_date": "2026-05-31", "security_desc": "Treasury Bonds", "avg_interest_rate_amt": "3.10"}
]}
"""

WORLD_BANK_JSON = """
[ {"page": 1, "pages": 1, "per_page": 1000, "total": 2},
  [ {"indicator": {"id": "NY.GDP.MKTP.CD"}, "country": {"id": "WLD"}, "date": "2024", "value": 105000000000000},
    {"indicator": {"id": "NY.GDP.MKTP.CD"}, "country": {"id": "WLD"}, "date": "2023", "value": null} ] ]
"""

BLS_JSON = """
{"Results": {"series": [{"seriesID": "CUUR0000SA0", "data": [
  {"year": "2026", "period": "M05", "value": "313.5"},
  {"year": "2026", "period": "M04", "value": "312.0"}
]}]}}
"""


def test_all_five_sources_registered():
    ids = {s.source_id for s in all_specs()}
    assert {"fred", "sec_edgar", "treasury", "world_bank", "bls"} <= ids


def test_treasury_stores_rates(dbs):
    res = TreasuryConnector().run(dbs.macro, transport=_stub(TREASURY_JSON), now=NOW)
    assert res.stored == 2 and res.documents == 1
    with sqlite3.connect(dbs.macro) as c:
        row = c.execute("SELECT indicator, value, event_date, source_id, content_hash "
                        "FROM macro_observations WHERE source_id='treasury' ORDER BY indicator").fetchone()
    assert row[0] == "Treasury Bonds" and row[1] == pytest.approx(3.10)
    assert row[2] == "2026-05-31" and row[3] == "treasury" and row[4]


def test_world_bank_skips_nulls(dbs):
    res = WorldBankConnector().run(dbs.macro, transport=_stub(WORLD_BANK_JSON),
                                   indicator="NY.GDP.MKTP.CD", now=NOW)
    assert res.stored == 1                       # the null observation is skipped
    with sqlite3.connect(dbs.macro) as c:
        row = c.execute("SELECT indicator, region, event_date FROM macro_observations "
                        "WHERE source_id='world_bank'").fetchone()
    assert row[0] == "NY.GDP.MKTP.CD" and row[1] == "WLD" and row[2] == "2024-12-31"


def test_bls_maps_periods_to_dates(dbs):
    res = BlsConnector().run(dbs.macro, transport=_stub(BLS_JSON), series_id="CUUR0000SA0", now=NOW)
    assert res.stored == 2
    with sqlite3.connect(dbs.macro) as c:
        dates = [r[0] for r in c.execute(
            "SELECT event_date FROM macro_observations WHERE source_id='bls' ORDER BY event_date").fetchall()]
    assert dates == ["2026-04-01", "2026-05-01"]


def test_macro_connectors_share_one_table(dbs):
    TreasuryConnector().run(dbs.macro, transport=_stub(TREASURY_JSON), now=NOW)
    BlsConnector().run(dbs.macro, transport=_stub(BLS_JSON), series_id="CUUR0000SA0", now=NOW)
    assert _count(dbs.macro) == 4                # 2 treasury + 2 bls, all in macro_observations

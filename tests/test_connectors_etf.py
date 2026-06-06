"""
S8 slice 5 — ETF issuer holdings connector (CSV → camel_sharia.db etf_holdings).
Header-tolerant; look-through to single-name exposure. Hermetic via stubbed transport.
"""
import sqlite3
import pytest

from data.source_registry import all_specs
from data.connectors.etf_holdings import EtfHoldingsConnector

NOW = "2026-06-06T00:00:00+00:00"


def _stub(payload: str):
    return lambda url: payload


# standard issuer layout + a cash row with no ticker (must be skipped)
SPUS_CSV = """Ticker,Name,Weight (%),Shares
AAPL,Apple Inc,8.50,1000
MSFT,Microsoft Corp,7.20,800
,US Dollar,1.30,
"""

# a different issuer's header layout — proves header tolerance
HLAL_CSV = """StockTicker,Security Name,% of Net Assets
NVDA,NVIDIA Corp,6.0
"""


def _run(dbs, csv, etf):
    return EtfHoldingsConnector().run(
        dbs.sharia, transport=_stub(csv),
        holdings_url=f"https://issuer.example/{etf}.csv", etf=etf, as_of="2026-05-31", now=NOW)


def test_etf_holdings_source_registered():
    assert "etf_holdings" in {s.source_id for s in all_specs()}


def test_spus_holdings_parsed_and_cash_row_skipped(dbs):
    res = _run(dbs, SPUS_CSV, "SPUS")
    assert res.stored == 2                         # AAPL, MSFT — the cash row (no ticker) is skipped
    with sqlite3.connect(dbs.sharia) as c:
        row = c.execute("SELECT holding_name, weight, shares, event_date, source_id, content_hash "
                        "FROM etf_holdings WHERE etf='SPUS' AND holding_ticker='AAPL'").fetchone()
    assert row[0] == "Apple Inc" and row[1] == pytest.approx(8.5) and row[2] == pytest.approx(1000)
    assert row[3] == "2026-05-31" and row[4] == "etf_holdings" and row[5]


def test_header_tolerance_across_issuers(dbs):
    res = _run(dbs, HLAL_CSV, "HLAL")
    assert res.stored == 1
    with sqlite3.connect(dbs.sharia) as c:
        row = c.execute("SELECT holding_ticker, weight FROM etf_holdings WHERE etf='HLAL'").fetchone()
    assert row[0] == "NVDA" and row[1] == pytest.approx(6.0)


def test_lookthrough_single_name_exposure(dbs):
    _run(dbs, SPUS_CSV, "SPUS")
    with sqlite3.connect(dbs.sharia) as c:
        names = [r[0] for r in c.execute(
            "SELECT holding_ticker FROM etf_holdings WHERE etf='SPUS' ORDER BY holding_ticker").fetchall()]
    assert names == ["AAPL", "MSFT"]               # the portfolio can see through SPUS to its names


def test_etf_holdings_idempotent(dbs):
    _run(dbs, SPUS_CSV, "SPUS")
    res2 = _run(dbs, SPUS_CSV, "SPUS")
    assert res2.stored == 0
    with sqlite3.connect(dbs.sharia) as c:
        total = c.execute("SELECT COUNT(*) FROM etf_holdings").fetchone()[0]
    assert total == 2

"""P2 pre-live hardening: full compact screen, doubtful persistence, manual-fill guard, shadow-phase guard."""
import pytest

from sharia.screener import Financials, screen_instrument, run_quarterly_rescreen
from sharia.whitelist import add_instrument, get_instrument


# ---- P2-D: the compact screener can run ALL 5 AAOIFI screens when given the data ----

def test_partial_screen_flags_unscreened_dimensions():
    r = screen_instrument(Financials("X", 1_000_000, 100_000, 100_000, 0.01))
    assert r.passed and r.full_screen is False
    assert "receivables_ratio" in r.unscreened and "prohibited_sector" in r.unscreened


def test_full_screen_catches_prohibited_sector():
    r = screen_instrument(Financials("X", 1_000_000, 100_000, 100_000, 0.01,
                                     receivables=0.0, total_assets=1_000_000, sector="gambling"))
    assert r.full_screen is True and r.unscreened == []
    assert not r.passed and any("sector" in s for s in r.reasons)


def test_full_screen_catches_receivables_breach():
    r = screen_instrument(Financials("X", 1_000_000, 100_000, 100_000, 0.01,
                                     receivables=900_000, total_assets=1_000_000, sector="tech"))
    assert r.full_screen is True and not r.passed
    assert any("receivables" in s for s in r.reasons)


def test_full_clean_name_passes_full_screen():
    r = screen_instrument(Financials("X", 1_000_000, 100_000, 100_000, 0.01,
                                     receivables=100_000, total_assets=1_000_000, sector="technology"))
    assert r.passed and r.full_screen is True and r.unscreened == []


# ---- P2-E: a quarterly rescreen marks doubtful names so they aren't left "compliant" ----

def test_quarterly_rescreen_marks_doubtful(dbs):
    db = dbs.sharia
    add_instrument(db, "DBT", "etf", approved_by="chiko", scan_id="s1")
    # 29% debt → doubtful watch band (passes, but must not stay 'compliant')
    run_quarterly_rescreen(db, lambda s: Financials(s, 1_000_000, 290_000, 0, 0.0))
    assert get_instrument(db, "DBT")["sharia_status"] == "doubtful"
    assert get_instrument(db, "DBT")["frozen"] == 0     # doubtful is a watch, not a freeze


# ---- P2-G: manual-fill records warnings + tags + writes atomically ----

def test_manual_fill_warns_on_off_whitelist_buy(dbs):
    from broker.manual import record_fill
    out = record_fill(dbs, symbol="NOTLISTED", side="buy", qty=1, price=10.0, ticket_id="t1")
    assert out["manual"] is True
    assert any("whitelist" in w for w in out["warnings"])


# ---- P2-F: shadow / non-enforcing Edge Proof is refused once live (phase >= 1) ----

def test_shadow_mode_refused_at_live_phase(dbs):
    from loop.driver import run_strategy_tick
    from loop.assembled import AssembledLoop
    from strategies.registry import StrategyRegistry
    from guardrail.constitution import PortfolioState
    loop = AssembledLoop(dbs, phase=1)
    with pytest.raises(ValueError):
        run_strategy_tick(dbs, StrategyRegistry(), PortfolioState(fund_usd=100, cash_usd=100),
                          symbols=["AAPL"], loop=loop, mode="shadow")

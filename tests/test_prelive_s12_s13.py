"""S12 per-portfolio book threading + S13 approval channel + manual-entry parser."""
from broker.paper import PaperBroker
from trader.portfolios.holdings import holdings, reconcile_to_fund
from guardrail.constitution import Action, ActionType, Decision, Thesis
from governance import approval, approval_channel
from broker import manual


def _buy(symbol="SPUS", notional=500.0):
    return Action(type=ActionType.TRADE, symbol=symbol, side="buy", notional_usd=notional,
                  instrument_type="etf",
                  thesis=Thesis(invalidation="x", profit_take="y", time_stop="z"), mode="paper")


# ---- S12: a fill with portfolio_id updates the fund book AND the per-portfolio book atomically ----

def test_fill_updates_portfolio_book_and_reconciles(dbs):
    b = PaperBroker(dbs.portfolio, dbs.market, allow_fallback_price=True)
    b.submit(_buy("SPUS", 500.0), Decision(allow=True, reason="ok"), portfolio_id="core")
    h = holdings(dbs, "core")
    assert len(h) == 1 and h[0]["symbol"] == "SPUS" and h[0]["qty"] == 500.0   # 500/$1 fallback
    # the per-portfolio book reconciles to the fund book (positions table = 500 SPUS)
    assert reconcile_to_fund(dbs, {"SPUS": 500.0}) == []


def test_fill_without_portfolio_id_leaves_portfolio_book_empty(dbs):
    b = PaperBroker(dbs.portfolio, dbs.market, allow_fallback_price=True)
    b.submit(_buy("SPUS", 500.0), Decision(allow=True, reason="ok"))   # no portfolio_id
    assert holdings(dbs, "core") == []


# ---- S13: inbound approve/veto channel ----

def test_approve_command_records_approval(dbs):
    approval.request_approval(dbs, "trade-1")
    r = approval_channel.handle_command(dbs, "approve trade-1", sender="chiko", founder_id="chiko")
    assert r.handled and r.approved is True
    assert approval.is_approved(dbs, "trade-1")


def test_veto_command_withholds(dbs):
    approval.request_approval(dbs, "trade-2")
    r = approval_channel.handle_command(dbs, "veto trade-2", sender="chiko", founder_id="chiko")
    assert r.handled and r.approved is False
    assert not approval.is_approved(dbs, "trade-2")


def test_non_founder_sender_is_ignored(dbs):
    approval.request_approval(dbs, "trade-3")
    r = approval_channel.handle_command(dbs, "approve trade-3", sender="stranger", founder_id="chiko")
    assert not r.handled and not approval.is_approved(dbs, "trade-3")


def test_unrecognised_command_is_noop(dbs):
    r = approval_channel.handle_command(dbs, "hello there", sender="chiko", founder_id="chiko")
    assert not r.handled


# ---- S13: manual-entry parser ----

def test_parse_fill_text_variants():
    assert manual.parse_fill_text("Buy 10 SPUS @ 41.20") == {"side": "buy", "symbol": "SPUS", "qty": 10, "price": 41.20}
    assert manual.parse_fill_text("Bought 10 shares of SPUS at $41.20")["side"] == "buy"
    assert manual.parse_fill_text("SELL SPUS 5 48.90") == {"side": "sell", "symbol": "SPUS", "qty": 5, "price": 48.90}


def test_parse_fill_text_rejects_ambiguous():
    assert manual.parse_fill_text("") is None
    assert manual.parse_fill_text("just some text") is None
    assert manual.parse_fill_text("buy SPUS") is None       # no qty/price → refuse, don't guess


def test_record_fill_from_text_writes_book(dbs):
    out = manual.record_fill_from_text(dbs, "Buy 10 SPUS @ 5.00", ticket_id="t9")
    assert out is not None and out["manual"] is True and out["position_qty"] == 10

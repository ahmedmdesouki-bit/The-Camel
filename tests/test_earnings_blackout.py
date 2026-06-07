"""Earnings-blackout rule (S8/S13): refuse opening into an earnings print; sells always allowed."""
from guardrail.earnings_blackout import in_blackout, is_blocked


def test_in_window_blocks():
    assert in_blackout(["2026-06-10"], "2026-06-09", window_days=2)      # 1 day before
    assert in_blackout(["2026-06-10"], "2026-06-12", window_days=2)      # 2 days after
    assert in_blackout(["2026-06-10"], "2026-06-10", window_days=0)      # the day itself


def test_outside_window_allows():
    assert not in_blackout(["2026-06-10"], "2026-06-15", window_days=2)


def test_empty_or_unknown_calendar_is_inert():
    assert not in_blackout([], "2026-06-10")
    assert not in_blackout(None, "2026-06-10")
    assert not in_blackout(["bad-date"], "2026-06-10")
    assert not in_blackout(["2026-06-10"], None)


def test_only_opening_sides_blocked():
    cal, day = ["2026-06-10"], "2026-06-10"
    assert is_blocked("buy", cal, day)
    assert is_blocked("increase", cal, day)
    assert not is_blocked("sell", cal, day)        # de-risking always allowed
    assert not is_blocked("close", cal, day)

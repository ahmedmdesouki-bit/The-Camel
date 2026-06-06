"""
S6a — dashboard + Telegram alerts + daily report delivery.
"""
import pytest
from dashboard.generate import build_dashboard_html, write_dashboard
from alerts.telegram import TelegramNotifier
from alerts.daily import send_daily_report
from data.store import store_price
from ledger.writer import append_entry
from sharia.whitelist import add_instrument, freeze_instrument


# ---------------- dashboard ----------------

def test_dashboard_renders_status_and_sections(dbs):
    h = build_dashboard_html(dbs, mode="paper")
    assert "The Camel" in h and "Read-only operator view" in h
    assert "GREEN" in h                       # fresh DBs, kill switch off
    for section in ("Positions", "Ledger", "Recent runs", "Guardrail events", "Sharia whitelist"):
        assert section in h

def test_dashboard_reflects_a_paper_trade(dbs):
    append_entry(dbs.portfolio, "DEPOSIT", "", 1000.0)
    append_entry(dbs.portfolio, "BUY", "SPUS", -300.0, ref="order_1")
    h = build_dashboard_html(dbs, mode="paper")
    assert "SPUS" in h and "BUY" in h
    assert "Cash balance: $700.00" in h       # 1000 - 300

def test_dashboard_shows_frozen_sharia_flag(dbs):
    add_instrument(dbs.sharia, "HLAL", "etf", approved_by="chiko", scan_id="s1")
    freeze_instrument(dbs.sharia, "HLAL", reason="drift")
    h = build_dashboard_html(dbs, mode="paper")
    assert "HLAL" in h and "YES" in h         # frozen flag rendered

def test_dashboard_escapes_html(dbs):
    # a malicious-looking symbol must be escaped, not injected
    add_instrument(dbs.sharia, "<script>", "etf", approved_by="x", scan_id="s2")
    h = build_dashboard_html(dbs, mode="paper")
    assert "<script>" not in h and "&lt;script&gt;" in h

def test_write_dashboard_to_file(dbs, tmp_path):
    out = str(tmp_path / "dash.html")
    write_dashboard(dbs, out)
    assert open(out, encoding="utf-8").read().startswith("<!doctype html>")


# ---------------- telegram (credential-safe stub) ----------------

def test_telegram_stub_without_creds():
    n = TelegramNotifier(token=None, chat_id=None)
    assert not n.configured
    r = n.send("hello")
    assert not r.sent and r.preview == "hello" and "stub" in r.reason

def test_telegram_configured_flag():
    assert TelegramNotifier(token="t", chat_id="c").configured

def test_telegram_send_never_raises_without_network():
    # configured but offline/invalid → must return a result, not raise
    n = TelegramNotifier(token="bad", chat_id="bad")
    r = n.send("x")
    assert r.preview == "x" and not r.sent     # reason set, no exception


# ---------------- daily report delivery ----------------

def test_send_daily_report_stub_carries_text(dbs):
    r = send_daily_report(dbs, mode="paper", notifier=TelegramNotifier(None, None))
    assert not r.sent
    assert "Camel Daily Health Report" in r.preview
    assert "System status: GREEN" in r.preview

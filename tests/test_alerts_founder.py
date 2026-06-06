"""
Founder-facing alerting harvested from Alaa's parallel build (S6):
WhatsApp/CallMeBot channel, the RED ALERT panic protocol, and the daily founder brief.
All credential-safe and network-free in tests.
"""
from alerts.whatsapp import WhatsAppNotifier
from alerts.telegram import TelegramNotifier
from alerts.redalert import check_red_alert, red_alert_message
from alerts.brief import build_founder_brief, send_founder_brief
from ledger.writer import append_entry


# ---------------- WhatsApp notifier (credential-safe stub) ----------------

def test_whatsapp_stub_without_creds():
    n = WhatsAppNotifier(phone=None, api_key=None)
    assert not n.configured
    r = n.send("hi")
    assert not r.sent and r.preview == "hi" and "stub" in r.reason


def test_whatsapp_configured_flag():
    assert WhatsAppNotifier(phone="966500000000", api_key="k").configured


def test_whatsapp_send_never_raises_without_network():
    n = WhatsAppNotifier(phone="bad", api_key="bad")
    r = n.send("x")
    assert r.preview == "x" and not r.sent       # returns a result, no exception


# ---------------- RED ALERT panic protocol ----------------

def test_red_alert_fires_on_big_drop_and_never_says_sell():
    alert = check_red_alert({"SCHD": -5.2, "SCHX": -0.4}, threshold_pct=-3.0)
    assert alert.triggered
    assert [b["symbol"] for b in alert.breaches] == ["SCHD"]
    msg = red_alert_message(alert).lower()
    assert "breathe" in msg and "hold" in msg
    # mentions selling only to FORBID a panic sell, and reframes the drop as a future buy signal
    assert "no panic sell" in msg
    assert "do not place any order" in msg
    assert "future buy signal" in msg


def test_red_alert_quiet_on_normal_day():
    alert = check_red_alert({"SCHD": -1.0, "SCHX": 0.5})
    assert not alert.triggered
    assert red_alert_message(alert) == ""


# ---------------- founder brief ----------------

def test_founder_brief_has_value_and_safety_posture(dbs):
    append_entry(dbs.portfolio, "DEPOSIT", "", 100.0)
    text = build_founder_brief(dbs, mode="paper")
    assert "THE CAMEL — Daily Brief" in text
    assert "Total value:" in text and "Cash drag:" in text
    assert "Live-money gate:" in text and "Live capital at risk: $0" in text


def test_founder_brief_appends_red_alert_when_triggered(dbs):
    append_entry(dbs.portfolio, "DEPOSIT", "", 100.0)
    quiet = build_founder_brief(dbs, mode="paper", price_moves={"SCHD": -0.5})
    assert "RED ALERT" not in quiet
    loud = build_founder_brief(dbs, mode="paper", price_moves={"SCHD": -4.0})
    assert "RED ALERT" in loud and "Breathe" in loud


def test_send_founder_brief_via_whatsapp_stub(dbs):
    r = send_founder_brief(dbs, mode="paper", notifier=WhatsAppNotifier(None, None))
    assert not r.sent and "THE CAMEL — Daily Brief" in r.preview


def test_send_founder_brief_via_telegram_stub(dbs):
    r = send_founder_brief(dbs, mode="paper", notifier=TelegramNotifier(None, None))
    assert not r.sent and "THE CAMEL — Daily Brief" in r.preview

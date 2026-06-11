"""
S17 — GPR connector (Caldara-Iacoviello Geopolitical Risk Index) + its wiring into the regime.
Injected transport, so no live web.
"""
from db.sqlite import connection
from data.connectors.gpr import GPRConnector, _to_event_date
from trader.regime.features import build_features
from trader.regime.classifier import classify, Regime


def test_to_event_date_formats():
    assert _to_event_date("2026M01") == "2026-01-01"
    assert _to_event_date("2026-03") == "2026-03-01"
    assert _to_event_date("2026/03/15") == "2026-03-15"
    assert _to_event_date("garbage") is None


def test_gpr_connector_parses_and_stores(dbs):
    csv = "month,GPR\n2026M01,210.5\n2026M02,95.0\nbad,\n"
    res = GPRConnector().run(dbs.macro, transport=lambda u: csv)
    assert res.stored == 2                                  # the undatable 'bad' row is dropped
    with connection(dbs.macro) as conn:
        rows = conn.execute("SELECT value, event_date FROM macro_observations WHERE series_id='GPR' "
                            "ORDER BY event_date").fetchall()
    assert [r["value"] for r in rows] == [210.5, 95.0]
    assert rows[0]["event_date"] == "2026-01-01"


def test_gpr_feature_picked_up(dbs):
    GPRConnector().run(dbs.macro, transport=lambda u: "month,GPR\n2026M01,260.0\n")
    assert build_features(dbs)["gpr"] == 260.0


def test_high_gpr_triggers_geopolitical_risk_off():
    res = classify({"gpr": 260.0})
    assert res.regime == Regime.GEOPOLITICAL_RISK_OFF
    assert any("gpr" in sg for sg in res.signals)


def test_benign_gpr_fires_no_signal():
    res = classify({"gpr": 90.0})                           # below GPR_HIGH -> no risk-off contribution
    assert res.regime == Regime.RECOVERY
    assert not any("gpr" in sg for sg in res.signals)


def test_absent_gpr_changes_nothing():
    assert classify({}).regime == Regime.UNKNOWN

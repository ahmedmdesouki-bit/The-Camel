"""
Dashboard re-skin to the Camel Design System (claude.ai/design handoff).

Locks in that the design tokens + component classes are applied AND that the re-skin did not break the
hard constraints: offline (no webfont/CDN imports), no JavaScript, self-contained, read-only.
"""
from dashboard.generate import build_dashboard_html


def test_design_tokens_and_component_classes_present(dbs):
    h = build_dashboard_html(dbs, mode="paper")
    # the three brand colours as CSS custom properties (engraved-seal palette)
    for token in ("--green-800:#0f3b34", "--gold-500:#c9a14a", "--sand-100:#f5f1e6"):
        assert token in h
    # the three type voices
    assert "--font-serif:" in h and "--font-mono:" in h and "--font-sans:" in h
    # design-system component classes are used in the markup
    for cls in ("cml-card", "cml-stat", "cml-badge", "cml-tab", "cml-gate", "cml-verdict", "cml-tick"):
        assert cls in h


def test_reskin_stays_offline_and_scriptless(dbs):
    h = build_dashboard_html(dbs, mode="paper")
    # offline: no webfont / CDN imports the design tool used (we fall back to system serif/sans/mono)
    assert "fonts.googleapis.com" not in h
    assert "unpkg.com" not in h and "@import" not in h
    # still no JS, no live fetch, no order entry (the read-only safety guarantee)
    assert "<script" not in h.lower()
    assert "fetch(" not in h and "localStorage" not in h and "<form" not in h.lower()
    assert "no order entry" in h

"""Smoke test for demo.py — the one-command tester entrypoint must keep working end-to-end."""
from importlib import import_module


def test_demo_runs_full_stack_and_writes_dashboard(tmp_path):
    demo = import_module("demo")
    out = tmp_path / "demo_run"
    rc = demo.main(out_dir=str(out), quiet=True)
    assert rc == 0
    dash = out / "camel-dashboard.html"
    assert dash.exists()
    html = dash.read_text(encoding="utf-8")
    assert "GREEN" in html or "RED" in html          # the mode banner rendered
    assert "<script>" not in html                      # read-only: no order entry / no JS

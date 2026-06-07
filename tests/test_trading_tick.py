"""P1-C/D/E — the production trading-tick entrypoint wires the Edge-gated assembled path:
Constitution-from-yaml (single phase source), an injected Budget Kernel, the assembled loop."""
from loop.jobs import run_trading_tick, _budget_kernel, _build_portfolio_state
from ledger.writer import append_entry


def _write_yaml(tmp_path, phase):
    p = tmp_path / "limits.yaml"
    p.write_text(f"phase: {phase}\nmax_position_pct: 0.20\nper_order_envelope_usd: 50\n", encoding="utf-8")
    return str(p)


def test_tick_reads_phase_from_yaml_and_injects_budget(dbs, tmp_path):
    append_entry(dbs.portfolio, "DEPOSIT", "", 1000.0)
    cfg = _write_yaml(tmp_path, phase=0)
    out = run_trading_tick(dbs, symbols=[], config_path=cfg, notional_per_trade=50.0)
    assert out["phase"] == 0                 # phase came from the founder-owned yaml (P1-D)
    assert out["budget_present"] is True     # the Budget Kernel was injected (P1-C)
    assert out["fund_usd"] == 1000.0
    assert isinstance(out["executed"], list)  # the assembled loop ran (P1-E)


def test_budget_kernel_is_bound_not_skipped(dbs):
    bk = _budget_kernel({"max_position_pct": 0.20}, fund=1000.0, notional=50.0)
    # a spend over the per-action cap (20% of 1000 = 200) is rejected → the kernel is real, not a no-op
    assert not bk.check(500.0, _state0()).allow
    assert bk.check(50.0, _state0()).allow


def _state0():
    from capital.budget_kernel import BudgetState
    return BudgetState()


def test_phase1_yaml_withholds_approval_by_default(dbs, tmp_path):
    # at phase 1 the assembled loop requires human approval; default withholds → nothing executes
    append_entry(dbs.portfolio, "DEPOSIT", "", 1000.0)
    cfg = _write_yaml(tmp_path, phase=1)
    out = run_trading_tick(dbs, symbols=["AAPL"], config_path=cfg)
    assert out["phase"] == 1
    assert out["executed"] == []             # fail-safe: no approval_fn → no live execution

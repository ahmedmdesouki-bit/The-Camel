"""
Dashboard generator (S6) — a self-contained HTML view of The Camel's live state.

Reads the SQLite DBs (no server needed) and renders one static HTML file: system status,
positions, cash/ledger, recent runs, guardrail events, and Sharia whitelist flags. The
operator view is READ-ONLY — there is no order entry from the dashboard (FR-V2).
Port to a live Supabase-backed page at S6+ when remote access is wanted.
"""
from __future__ import annotations
import html
from typing import List

from db.paths import CamelDbs
from db.sqlite import connection
from ops.health_monitor import check


def _rows(db_path: str, sql: str) -> List[dict]:
    with connection(db_path) as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


def _esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


def _table(headers: List[str], rows: List[List]) -> str:
    if not rows:
        return "<p class='empty'>none</p>"
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def build_dashboard_html(dbs: CamelDbs, mode: str = "paper") -> str:
    report = check(dbs, mode=mode)
    color = {"GREEN": "#1a7f37", "YELLOW": "#9a6700", "RED": "#cf222e", "BLACK": "#24292f"}.get(
        report.status, "#57606a")

    positions = _rows(dbs.portfolio, "SELECT symbol, qty, avg_cost, market_value, unrealized_pnl FROM positions ORDER BY symbol")
    ledger = _rows(dbs.portfolio, "SELECT ts, type, symbol, amount, balance_after FROM ledger ORDER BY id DESC LIMIT 15")
    runs = _rows(dbs.portfolio, "SELECT id, started_at, outcome FROM runs ORDER BY id DESC LIMIT 10")
    guard = _rows(dbs.portfolio, "SELECT ts, reason, limit_hit FROM guardrail_events ORDER BY id DESC LIMIT 10")
    whitelist = _rows(dbs.sharia, "SELECT symbol, sharia_status, frozen FROM whitelist ORDER BY symbol")

    bal = ledger[0]["balance_after"] if ledger else 0.0

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>The Camel — Dashboard</title>
<style>
 body{{font-family:system-ui,Arial,sans-serif;margin:24px;color:#1f2328;background:#f6f8fa}}
 h1{{margin:0 0 4px}} .sub{{color:#57606a;margin:0 0 16px}}
 .status{{display:inline-block;padding:6px 14px;border-radius:6px;color:#fff;font-weight:700;background:{color}}}
 .card{{background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:14px 16px;margin:14px 0}}
 table{{border-collapse:collapse;width:100%;font-size:14px}} th,td{{border:1px solid #d0d7de;padding:6px 8px;text-align:left}}
 th{{background:#f6f8fa}} .empty{{color:#8c959f;font-style:italic}} .kpi{{font-size:20px;font-weight:700}}
</style></head><body>
<h1>🐫 The Camel</h1>
<p class="sub">Read-only operator view · mode: <b>{_esc(mode)}</b></p>
<p><span class="status">{_esc(report.status)}</span>
   &nbsp; Issues: {_esc(', '.join(report.issues) or 'none')}</p>

<div class="card"><div class="kpi">Cash balance: ${_esc(f'{bal:.2f}')}</div>
  Open positions: {len(positions)} · Paper only · Live capital at risk: $0</div>

<div class="card"><h3>Positions</h3>
 {_table(['Symbol','Qty','Avg cost','Mkt value','Unreal. P&L'],
         [[p['symbol'],p['qty'],p['avg_cost'],p['market_value'],p['unrealized_pnl']] for p in positions])}</div>

<div class="card"><h3>Ledger (last 15)</h3>
 {_table(['Time','Type','Symbol','Amount','Balance after'],
         [[l['ts'],l['type'],l['symbol'],l['amount'],l['balance_after']] for l in ledger])}</div>

<div class="card"><h3>Recent runs</h3>
 {_table(['Run','Started','Outcome'], [[r['id'],r['started_at'],r['outcome']] for r in runs])}</div>

<div class="card"><h3>Guardrail events (last 10)</h3>
 {_table(['Time','Reason','Limit hit'], [[g['ts'],g['reason'],g['limit_hit']] for g in guard])}</div>

<div class="card"><h3>Sharia whitelist</h3>
 {_table(['Symbol','Status','Frozen'],
         [[w['symbol'],w['sharia_status'],'YES' if w['frozen'] else ''] for w in whitelist])}</div>
</body></html>"""


def write_dashboard(dbs: CamelDbs, out_path: str, mode: str = "paper") -> str:
    htmls = build_dashboard_html(dbs, mode=mode)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(htmls)
    return out_path

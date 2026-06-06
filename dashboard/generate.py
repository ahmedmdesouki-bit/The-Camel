"""
Dashboard generator (S6 → enhanced after the Alaa cross-build review).

Renders ONE static, self-contained, READ-ONLY HTML page from the snapshot built by
`dashboard/snapshot.py`. Design choices that distinguish this from a browser-localStorage
dashboard:

  * Server-side render from the seven SQLite DBs — NO live web fetch, NO CORS proxy, NO
    client-side source of truth. Deterministic and offline (works with the file opened
    directly; no server needed). The operator view is read-only — there is no order entry
    (FR-V2).
  * It surfaces the **decisions**, not just the holdings: Edge-Proof verdicts and the
    Constitution's rejections-with-reasons are first-class panels — the rejections are the
    whole point of the system. Plus the current macro regime and the live-money safety posture.
  * Every DB-derived value is HTML-escaped (XSS-safe even for a hostile ticker symbol).
  * Tabbed views via a tiny vanilla script, with a no-JS fallback (all views visible).

Visual ground borrowed from Alaa's parallel build (deep-green / antique-gold palette, card
layout), re-implemented with system fonts so it stays fully offline, and re-pointed at our
real governed state. Port to a Supabase-backed live page at S6+/S10 when remote access is wanted.
"""
from __future__ import annotations

import html
from typing import List

from db.paths import CamelDbs
from dashboard.snapshot import build_snapshot

_STATUS_COLOR = {"GREEN": "#1a7f37", "YELLOW": "#9a6700", "RED": "#cf222e", "BLACK": "#24292f"}


def _esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


def _money(v) -> str:
    try:
        return f"${float(v):,.2f}"
    except (TypeError, ValueError):
        return "—"


def _signed(v) -> str:
    try:
        f = float(v)
        return f"{'+' if f >= 0 else '-'}${abs(f):,.2f}"
    except (TypeError, ValueError):
        return "—"


def _pnl_color(v) -> str:
    try:
        return "var(--up)" if float(v) >= 0 else "var(--down)"
    except (TypeError, ValueError):
        return "var(--muted)"


def _table(headers: List[str], rows: List[List], empty: str = "none") -> str:
    if not rows:
        return f"<p class='empty'>{_esc(empty)}</p>"
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


# ────────────────────────────────────────────────────────── panels ──

def _overview(s: dict) -> str:
    k, g = s["kpis"], s["governance"]
    status = s["health"]["status"]
    color = _STATUS_COLOR.get(status, "#57606a")
    issues = ", ".join(s["health"]["issues"]) or "none"
    drag = k["cash_drag_pct"]
    drag_warn = (drag is not None and isinstance(drag, (int, float)) and drag > 10)

    kpis = "".join(f"""
      <div class="kpi-card">
        <div class="kpi-label">{_esc(label)}</div>
        <div class="kpi-value" style="color:{color2}">{val}</div>
        <div class="kpi-sub">{_esc(sub)}</div>
      </div>""" for label, val, color2, sub in [
        ("Total value", _money(k["total_value"]), "var(--ink)", f"{k['open_positions']} open positions"),
        ("Cash", _money(k["cash"]), "var(--ink)", f"Cash balance: {_money(k['cash'])}"),
        ("Unrealised P&L", _signed(k["unrealized_pnl"]), _pnl_color(k["unrealized_pnl"]), "mark-to-market"),
        ("Realised P&L", _signed(k["realized_pnl"]), _pnl_color(k["realized_pnl"]), "booked on sells"),
        ("Cash drag", f"{_esc(drag)}%", "var(--down)" if drag_warn else "var(--ink)",
         "⚠ idle cash > 10%" if drag_warn else "within range"),
        ("Live capital at risk", _money(g["live_at_risk"]), "var(--up)", "paper only · $0"),
    ])

    gate = "".join(
        f"<li class='{'ok' if it['ok'] else 'bad'}'>{'✅' if it['ok'] else '❌'} {_esc(it['label'])}</li>"
        for it in g["gate_items"])

    return f"""
    <div class="view active" data-view="overview">
      <div class="status-row">
        <span class="status-pill" style="background:{color}">{_esc(status)}</span>
        <span class="status-meta">Mode: <b>{_esc(s['mode'])}</b> · {_esc(g['phase_label'])}
          · Kill switch: <b>{_esc(g['kill_switch'])}</b> · Issues: {_esc(issues)}</span>
      </div>
      <div class="kpi-grid">{kpis}</div>
      <div class="card">
        <h3>Live-money safety posture <span class="badge">{g['gate_passed']}/{g['gate_total']} clear</span></h3>
        <p class="hint">Honest booleans — each is a real fact, not a self-scored checkbox. Live trading stays
          blocked until the founder flips a phase flag.</p>
        <ul class="gate">{gate}</ul>
      </div>
    </div>"""


def _portfolio(s: dict) -> str:
    positions = s["positions"]
    pv = s["kpis"]["positions_value"] or 0
    rows = []
    for p in positions:
        alloc = (float(p["market_value"] or 0) / pv * 100) if pv else 0
        bar = f"<div class='bar'><span style='width:{min(100, alloc):.0f}%'></span></div>"
        rows.append([
            f"<span class='tick'>{_esc(p['symbol'])}</span>",
            _esc(p["qty"]), _money(p["avg_cost"]), _money(p["market_price"]), _money(p["market_value"]),
            f"<span style='color:{_pnl_color(p['unrealized_pnl'])};font-weight:700'>{_signed(p['unrealized_pnl'])}</span>",
            f"{bar}<span class='alloc'>{alloc:.0f}%</span>",
        ])
    return f"""
    <div class="view" data-view="portfolio">
      <div class="card">
        <h3>Positions</h3>
        {_table(['Symbol','Qty','Avg cost','Mkt price','Mkt value','Unreal. P&L','Allocation'], rows,
                empty='no open positions — paper book is flat')}
      </div>
    </div>"""


def _decisions(s: dict) -> str:
    # Edge-Proof verdicts
    erows = []
    for e in s["edge_decisions"]:
        verdict = ("<span class='v-allow'>✅ ALLOWED</span>" if e["trade_allowed"]
                   else "<span class='v-block'>⛔ BLOCKED</span>")
        erows.append([
            _esc(e["ts"]), f"<span class='tick'>{_esc(e['symbol'])}</span>", _esc(e["signal"]),
            verdict, _esc(e["reason"]),
            _esc(e["hit_rate"]), _esc(e["sample_size"]), _esc(e["confidence"]),
        ])
    edge_tbl = _table(
        ['Time', 'Symbol', 'Signal', 'Edge verdict', 'Reason', 'Hit-rate', 'Sample', 'Confidence'],
        erows, empty='no Edge-Proof decisions logged yet (no strategy has run)')

    # Constitution guardrail decisions — rejections-with-reasons
    grows = []
    for g in s["guardrail"]:
        verdict = ("<span class='v-block'>⛔ BLOCKED</span>" if g["blocked"]
                   else "<span class='v-allow'>✅ allowed</span>")
        grows.append([
            _esc(g["ts"]), verdict, f"<span class='tick'>{_esc(g['symbol'])}</span>",
            _esc(g["reason"]), f"<code>{_esc(g['limit_hit'])}</code>" if g["limit_hit"] else "",
        ])
    guard_tbl = _table(['Time', 'Decision', 'Symbol', 'Reason', 'Limit hit'], grows,
                       empty='no guardrail events yet')

    return f"""
    <div class="view" data-view="decisions">
      <div class="card">
        <h3>Edge-Proof decisions</h3>
        <p class="hint">No trade proceeds without a passing EdgeReport. These are the verdicts — including
          the rejections, which are the whole point.</p>
        {edge_tbl}
      </div>
      <div class="card">
        <h3>Guardrail events <span class="badge">Constitution</span></h3>
        <p class="hint">Every consequential action is run through the deterministic Constitution.
          Blocked actions are shown with the exact reason and the limit that fired.</p>
        {guard_tbl}
      </div>
    </div>"""


def _regime(s: dict) -> str:
    r = s["regime"]
    if r:
        conf = r["confidence"]
        signals = "".join(f"<span class='chip'>{_esc(x)}</span>" for x in r["signals"]) or "<span class='empty'>none</span>"
        current = f"""
        <div class="regime-now">
          <div class="regime-label">CURRENT REGIME</div>
          <div class="regime-value">{_esc(r['regime'])}</div>
          <div class="regime-conf">confidence {_esc(conf)} · classified {_esc(r['classified_at'])}</div>
          <div class="chips">{signals}</div>
        </div>"""
    else:
        current = "<p class='empty'>no regime classified yet (needs macro observations — S9)</p>"

    hrows = [[_esc(h["classified_at"]), _esc(h["regime"]), _esc(h["confidence"])] for h in s["regime_history"]]
    return f"""
    <div class="view" data-view="regime">
      <div class="card">
        <h3>Macro regime</h3>
        {current}
      </div>
      <div class="card">
        <h3>Regime history</h3>
        {_table(['Classified at', 'Regime', 'Confidence'], hrows, empty='no history yet')}
      </div>
    </div>"""


def _sharia(s: dict) -> str:
    rows = []
    for w in s["whitelist"]:
        frozen = "<span class='v-block'>YES</span>" if w["frozen"] else ""
        rows.append([f"<span class='tick'>{_esc(w['symbol'])}</span>",
                     _esc(w["sharia_status"]), frozen])
    return f"""
    <div class="view" data-view="sharia">
      <div class="card">
        <h3>Sharia whitelist</h3>
        <p class="hint">Only whitelisted, compliant, non-frozen instruments are tradeable. Frozen names are
          close-only. (Full AAOIFI ratios land at S9 — debt/30%, liquidity/67%, ≤5% non-compliant revenue.)</p>
        {_table(['Symbol', 'Status', 'Frozen'], rows, empty='whitelist empty')}
      </div>
    </div>"""


def _ops(s: dict) -> str:
    checks = s["health"]["checks"]
    crows = [[_esc(k), _esc(v)] for k, v in checks.items()]
    runs = [[_esc(r.get("id")), _esc(r.get("started_at")), _esc(r.get("phase")), _esc(r.get("outcome"))]
            for r in s["runs"]]
    ledger = [[_esc(l["ts"]), _esc(l["type"]), f"<span class='tick'>{_esc(l['symbol'])}</span>",
               _money(l["amount"]), _money(l["balance_after"])] for l in s["ledger"]]
    return f"""
    <div class="view" data-view="ops">
      <div class="card"><h3>Recent runs</h3>
        {_table(['Run', 'Started', 'Phase', 'Outcome'], runs, empty='no runs yet')}</div>
      <div class="card"><h3>Ledger</h3>
        {_table(['Time', 'Type', 'Symbol', 'Amount', 'Balance after'], ledger, empty='ledger empty')}</div>
      <div class="card"><h3>Health checks</h3>
        {_table(['Check', 'Result'], crows)}</div>
    </div>"""


_NAV = [("overview", "Overview"), ("portfolio", "Portfolio"), ("decisions", "Decisions"),
        ("regime", "Regime"), ("sharia", "Sharia"), ("ops", "Ops")]


def build_dashboard_html(dbs: CamelDbs, mode: str = "paper") -> str:
    s = build_snapshot(dbs, mode=mode)
    # CSS-only tab switcher: hidden radios + label nav + :checked ~ sibling rules.
    # No JavaScript → fully static, works with JS disabled, and no <script> tag to inject through.
    radios = "".join(
        f"<input type='radio' name='cv' id='cv-{vid}' class='vradio'{' checked' if i == 0 else ''}>"
        for i, (vid, _) in enumerate(_NAV))
    nav = "".join(
        f"<label class='nav-btn' for='cv-{vid}'>{_esc(label)}</label>" for vid, label in _NAV)
    view_css = "\n".join(
        f" #cv-{vid}:checked ~ main .view[data-view=\"{vid}\"]{{display:block}}\n"
        f" #cv-{vid}:checked ~ nav label[for=\"cv-{vid}\"]{{background:#fff;color:var(--green);"
        f"box-shadow:0 -2px 0 var(--gold) inset}}"
        for vid, _ in _NAV)
    views = (_overview(s) + _portfolio(s) + _decisions(s) + _regime(s) + _sharia(s) + _ops(s))

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Camel — Operator Dashboard</title>
<style>
 :root {{
   --green:#0f3b34; --green2:#1a3e2c; --gold:#c9a14a; --parch:#f5f1e6; --ink:#262626;
   --muted:rgba(38,38,38,.5); --up:#1a7f37; --down:#c13c1e; --line:rgba(38,38,38,.12);
 }}
 *{{box-sizing:border-box}}
 body{{font-family:'Iowan Old Style',Georgia,'Times New Roman',serif;margin:0;color:var(--ink);
   background:linear-gradient(160deg,#efe9da,#f5f1e6);}}
 header{{background:linear-gradient(135deg,var(--green),var(--green2));color:var(--parch);
   padding:20px 28px;box-shadow:0 2px 14px rgba(0,0,0,.15)}}
 header h1{{margin:0;font-size:26px;letter-spacing:.06em}}
 header .tag{{margin:4px 0 0;font-size:12px;color:rgba(245,241,230,.7);letter-spacing:.04em}}
 nav{{display:flex;gap:4px;flex-wrap:wrap;padding:10px 24px 0;background:transparent;position:sticky;top:0;
   backdrop-filter:blur(6px);z-index:5}}
 .vradio{{display:none}}
 .nav-btn{{font:inherit;font-size:13px;font-weight:700;letter-spacing:.03em;cursor:pointer;
   border:1px solid var(--line);border-bottom:none;background:rgba(255,255,255,.45);color:var(--muted);
   padding:9px 16px;border-radius:8px 8px 0 0;user-select:none}}
 main{{padding:18px 24px 48px;max-width:1100px;margin:0 auto}}
 .view{{display:none;animation:fade .2s ease}}
{view_css}
 @keyframes fade{{from{{opacity:0;transform:translateY(4px)}}to{{opacity:1}}}}
 .card{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:14px 0;
   box-shadow:0 1px 3px rgba(0,0,0,.04)}}
 .card h3{{margin:0 0 6px;font-size:15px;color:var(--green);letter-spacing:.03em}}
 .hint{{margin:0 0 12px;font-size:12px;color:var(--muted);line-height:1.5}}
 .badge{{font-size:10px;font-weight:800;background:rgba(201,161,74,.18);color:#7a5a10;
   padding:2px 8px;border-radius:10px;margin-left:6px;vertical-align:middle}}
 table{{border-collapse:collapse;width:100%;font-size:13px}}
 th,td{{border-bottom:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:middle}}
 th{{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:800}}
 tbody tr:hover{{background:rgba(15,59,52,.03)}}
 .tick{{font-weight:800;color:var(--green)}}
 .empty{{color:var(--muted);font-style:italic;padding:6px 0}}
 .status-row{{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:8px 0 16px}}
 .status-pill{{color:#fff;font-weight:800;padding:6px 16px;border-radius:8px;letter-spacing:.08em}}
 .status-meta{{font-size:13px;color:var(--muted)}}
 .kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:6px}}
 .kpi-card{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
 .kpi-label{{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:800}}
 .kpi-value{{font-size:24px;font-weight:800;margin:4px 0 2px}}
 .kpi-sub{{font-size:11px;color:var(--muted)}}
 .gate{{list-style:none;margin:0;padding:0}}
 .gate li{{padding:6px 0;font-size:13px;border-bottom:1px solid var(--line)}}
 .gate li.bad{{color:var(--down)}} .gate li.ok{{color:var(--up)}}
 .v-allow{{color:var(--up);font-weight:800}} .v-block{{color:var(--down);font-weight:800}}
 .bar{{display:inline-block;width:70px;height:7px;background:rgba(38,38,38,.1);border-radius:4px;
   overflow:hidden;vertical-align:middle;margin-right:6px}}
 .bar span{{display:block;height:100%;background:var(--gold)}}
 .alloc{{font-size:11px;color:var(--muted)}}
 code{{background:rgba(38,38,38,.06);padding:1px 5px;border-radius:4px;font-size:11px}}
 .regime-now{{padding:6px 0}}
 .regime-label{{font-size:11px;font-weight:800;letter-spacing:.08em;color:var(--muted)}}
 .regime-value{{font-size:28px;font-weight:800;color:var(--green);margin:2px 0}}
 .regime-conf{{font-size:12px;color:var(--muted)}}
 .chips{{margin-top:10px}}
 .chip{{display:inline-block;font-size:11px;font-weight:700;background:rgba(15,59,52,.08);color:var(--green);
   padding:3px 10px;border-radius:12px;margin:0 6px 6px 0}}
 footer{{text-align:center;font-size:11px;color:var(--muted);padding:18px}}
</style></head>
<body>
<header>
  <h1>🐫 The Camel</h1>
  <p class="tag">Read-only operator view · LLM proposes · Math tests · Guardrails decide · Humans approve · Autonomy earned</p>
</header>
{radios}
<nav>{nav}</nav>
<main>{views}</main>
<footer>Static read-only snapshot · no live fetch · no order entry · paper only.
  Not financial, legal, or Sharia advice.</footer>
</body></html>"""


def write_dashboard(dbs: CamelDbs, out_path: str, mode: str = "paper") -> str:
    htmls = build_dashboard_html(dbs, mode=mode)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(htmls)
    return out_path

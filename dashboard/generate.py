"""
Dashboard generator (S6 → Dashboard v2 → re-skinned to the Camel Design System).

Renders ONE static, self-contained, READ-ONLY HTML page from the snapshot built by
`dashboard/snapshot.py`, styled to the **Camel Design System** (claude.ai/design handoff):
engraved-seal malachite-green + antique-gold on warm parchment, three type voices (serif prose,
sans UI labels, **mono for every figure**), flat instrument-panel cards with hairline rules.

The hard constraints are preserved (they are load-bearing for the read-only safety guarantee, and
the design system explicitly notes the product renderer stays offline on system serifs):
  * server-side render from the 7 DBs — NO live fetch, NO CORS proxy, NO client source of truth;
  * **no `<script>` / no JS** — tabs are CSS-only (hidden radios), the kill-switch is a read-only
    status (not an interactive toggle), and there is no order entry;
  * design tokens are inlined as CSS custom properties; webfonts are NOT imported — the token font
    stacks fall back to system serif/sans/mono so the file works fully offline;
  * every DB-derived value is HTML-escaped (XSS-safe even for a hostile ticker symbol).

It surfaces the **decisions** — Edge-Proof verdicts + Constitution rejections-with-reasons — plus the
regime and the live-money safety posture, not just holdings.
"""
from __future__ import annotations

import html
from typing import List

from db.paths import CamelDbs
from dashboard.snapshot import build_snapshot

# health status → design "signal" tokens
_STATUS_VAR = {"GREEN": "var(--signal-green)", "YELLOW": "var(--signal-yellow)",
               "RED": "var(--signal-red)", "BLACK": "var(--signal-black)"}


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
        return f"{'+' if f >= 0 else '−'}${abs(f):,.2f}"
    except (TypeError, ValueError):
        return "—"


def _pnl_class(v) -> str:
    try:
        return "cml-up" if float(v) >= 0 else "cml-down"
    except (TypeError, ValueError):
        return "k-faint"


def _table(headers: List[str], rows: List[List], empty: str = "none") -> str:
    if not rows:
        return f"<p class='k-empty'>{_esc(empty)}</p>"
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table class='k-table'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _card(title: str, body: str, *, hint: str = "", badge: str = "") -> str:
    badge_html = f" {badge}" if badge else ""
    hint_html = f"<p class='cml-card__hint'>{_esc(hint)}</p>" if hint else ""
    return (f"<div class='cml-card'><div class='cml-card__head'>"
            f"<h3 class='cml-card__title'>{_esc(title)}</h3>{badge_html}</div>{hint_html}{body}</div>")


def _badge(text: str, tone: str = "gold") -> str:
    return f"<span class='cml-badge cml-badge--{tone}'>{_esc(text)}</span>"


def _verdict(allowed: bool, allow_label: str, block_label: str) -> str:
    if allowed:
        return f"<span class='cml-verdict cml-verdict--allow'>✓ {_esc(allow_label)}</span>"
    return f"<span class='cml-verdict cml-verdict--block'>⛔ {_esc(block_label)}</span>"


def _tick(sym) -> str:
    return f"<span class='cml-tick'>{_esc(sym)}</span>"


def _fig(v) -> str:
    return f"<span class='k-fig'>{_esc(v)}</span>"


# ────────────────────────────────────────────────────────── panels ──

def _overview(s: dict) -> str:
    k, g = s["kpis"], s["governance"]
    drag = k["cash_drag_pct"]
    drag_warn = isinstance(drag, (int, float)) and drag > 10

    cards = [
        ("Total value", _money(k["total_value"]), "k-fig", f"{k['open_positions']} open positions"),
        ("Cash", _money(k["cash"]), "k-fig", f"Cash balance: {_money(k['cash'])}"),
        ("Unrealised P&L", _signed(k["unrealized_pnl"]), _pnl_class(k["unrealized_pnl"]), "mark-to-market"),
        ("Realised P&L", _signed(k["realized_pnl"]), _pnl_class(k["realized_pnl"]), "booked on sells"),
        ("Cash drag", f"{_esc(drag)}%", "k-gold" if drag_warn else "k-fig",
         "⚠ idle cash > 10%" if drag_warn else "within range"),
        ("Live capital at risk", _money(g["live_at_risk"]), "cml-up", "paper only · $0"),
    ]
    kpis = "".join(
        f"<div class='cml-stat'><div class='cml-stat__label'>{_esc(label)}</div>"
        f"<div class='cml-stat__value {cls}'>{val}</div>"
        f"<div class='cml-stat__sub'>{_esc(sub)}</div></div>"
        for label, val, cls, sub in cards)

    gate = "".join(
        f"<li class='cml-gate__item'><span class='cml-gate__mark cml-gate__mark--{'ok' if it['ok'] else 'bad'}'>"
        f"{'✓' if it['ok'] else '✕'}</span>{_esc(it['label'])}</li>"
        for it in g["gate_items"])

    posture = _card(
        "Live-money safety posture",
        f"<ul class='cml-gate'>{gate}</ul>",
        hint="Honest booleans — each is a real fact, not a self-scored checkbox. Live trading stays "
             "blocked until the founder flips a phase flag.",
        badge=_badge(f"{g['gate_passed']}/{g['gate_total']} clear", "gold"))
    return f"<div class='view active' data-view='overview'><div class='k-stack'>" \
           f"<div class='k-kpi-grid'>{kpis}</div>{posture}</div></div>"


def _portfolio(s: dict) -> str:
    pv = s["kpis"]["positions_value"] or 0
    rows = []
    for p in s["positions"]:
        alloc = (float(p["market_value"] or 0) / pv * 100) if pv else 0
        bar = (f"<span class='k-alloc'><span class='k-bar'>"
               f"<span style='width:{min(100, alloc):.0f}%'></span></span>{alloc:.0f}%</span>")
        rows.append([
            _tick(p["symbol"]), _fig(p["qty"]), _fig(_money(p["avg_cost"])), _fig(_money(p["market_price"])),
            _fig(_money(p["market_value"])),
            f"<span class='k-fig {_pnl_class(p['unrealized_pnl'])}'>{_signed(p['unrealized_pnl'])}</span>", bar,
        ])
    tbl = _table(['Symbol', 'Qty', 'Avg cost', 'Mkt price', 'Mkt value', 'Unreal. P&L', 'Allocation'],
                 rows, empty='no open positions — paper book is flat')
    return f"<div class='view' data-view='portfolio'>" \
           f"{_card('Positions', tbl, hint='Whole-share, long-only, Sharia-screened book.')}</div>"


def _decisions(s: dict) -> str:
    erows = [[
        _esc(e["ts"]), _tick(e["symbol"]), f"<span class='k-mono-sm'>{_esc(e['signal'])}</span>",
        _verdict(e["trade_allowed"], "ALLOWED", "BLOCKED"), _esc(e["reason"]),
        _fig(e["hit_rate"]), _fig(f"n={e['sample_size']}"), _fig(e["confidence"]),
    ] for e in s["edge_decisions"]]
    edge = _card(
        "Edge-Proof decisions",
        _table(['Time', 'Symbol', 'Signal', 'Edge verdict', 'Reason', 'Hit-rate', 'Sample', 'Conf.'],
               erows, empty='no Edge-Proof decisions logged yet (no strategy has run)'),
        hint="No trade proceeds without a passing EdgeReport. These are the verdicts — including the "
             "rejections, which are the whole point.",
        badge=_badge("Evidence gate", "gold"))

    grows = [[
        _esc(g["ts"]), _verdict(not g["blocked"], "allowed", "BLOCKED"), _tick(g["symbol"]),
        _esc(g["reason"]), f"<code class='k-code'>{_esc(g['limit_hit'])}</code>" if g["limit_hit"] else "",
    ] for g in s["guardrail"]]
    guard = _card(
        "Guardrail events",
        _table(['Time', 'Decision', 'Symbol', 'Reason', 'Limit hit'], grows, empty='no guardrail events yet'),
        hint="Every consequential action runs through the deterministic Constitution. Blocked actions "
             "show the exact reason and the limit that fired.",
        badge=_badge("Constitution", "green"))
    return f"<div class='view' data-view='decisions'><div class='k-stack'>{edge}{guard}</div></div>"


def _regime(s: dict) -> str:
    r = s["regime"]
    if r:
        chips = "".join(f"<span class='k-chip'>{_esc(x)}</span>" for x in r["signals"]) \
            or "<span class='k-empty'>none</span>"
        now = (f"<div class='cml-eyebrow'>Current regime</div>"
               f"<div class='k-regime-val'>{_esc(r['regime'])}</div>"
               f"<div class='k-regime-conf'>confidence {_esc(r['confidence'])} · classified {_esc(r['classified_at'])}</div>"
               f"<div class='k-chips'>{chips}</div>")
    else:
        now = "<p class='k-empty'>no regime classified yet (needs macro observations — S9)</p>"
    hist = _table(['Classified at', 'Regime', 'Confidence'],
                  [[_esc(h["classified_at"]), _esc(h["regime"]), _fig(h["confidence"])] for h in s["regime_history"]],
                  empty='no history yet')
    return f"<div class='view' data-view='regime'><div class='k-stack'>" \
           f"{_card('Macro regime', now)}{_card('Regime history', hist)}</div></div>"


def _sharia(s: dict) -> str:
    rows = []
    for w in s["whitelist"]:
        if w["frozen"]:
            status = _badge(_esc(w["sharia_status"]), "down")
            trade = "<span class='cml-down k-fig'>close-only · YES (frozen)</span>"
        else:
            status = _badge(_esc(w["sharia_status"]) or "compliant", "up")
            trade = "<span class='k-faint'>tradeable</span>"
        rows.append([_tick(w["symbol"]), status, trade])
    tbl = _table(['Symbol', 'Status', 'Frozen / tradeability'], rows, empty='whitelist empty')
    return f"<div class='view' data-view='sharia'>" + _card(
        "Sharia whitelist", tbl,
        hint="Only whitelisted, compliant, non-frozen instruments are tradeable. Frozen names are "
             "close-only. (Full AAOIFI ratios at S9 — debt ≤30%, liquidity ≤67%, ≤5% non-compliant revenue.)"
    ) + "</div>"


def _ops(s: dict) -> str:
    runs = [[f"<span class='k-mono-sm'>{_esc(r.get('id'))}</span>", _esc(r.get("started_at")),
             _badge(_esc(r.get("phase")), "neutral"), _esc(r.get("outcome"))] for r in s["runs"]]
    ledger = [[_esc(l["ts"]), f"<span class='k-mono-sm'>{_esc(l['type'])}</span>", _tick(l["symbol"]),
               f"<span class='k-fig {_pnl_class(l['amount'])}'>{_money(l['amount'])}</span>",
               _fig(_money(l["balance_after"]))] for l in s["ledger"]]
    checks = [[_esc(k), f"<span class='cml-up k-fig'>{_esc(v)}</span>"] for k, v in s["health"]["checks"].items()]
    return (f"<div class='view' data-view='ops'><div class='k-stack'>"
            f"{_card('Recent runs', _table(['Run', 'Started', 'Phase', 'Outcome'], runs, empty='no runs yet'))}"
            f"{_card('Ledger', _table(['Time', 'Type', 'Symbol', 'Amount', 'Balance after'], ledger, empty='ledger empty'), badge=_badge('SHA-256 hash-chain', 'gold'))}"
            f"{_card('Health checks', _table(['Check', 'Result'], checks))}"
            f"</div></div>")


_NAV = [("overview", "Overview"), ("portfolio", "Portfolio"), ("decisions", "Decisions"),
        ("regime", "Regime"), ("sharia", "Sharia"), ("ops", "Ops")]


def build_dashboard_html(dbs: CamelDbs, mode: str = "paper") -> str:
    s = build_snapshot(dbs, mode=mode)
    status = s["health"]["status"]
    g = s["governance"]
    halted = g["kill_switch"] == "HALTED" or status == "BLACK"
    status_var = _STATUS_VAR.get(status, "var(--signal-green)")
    issues = ", ".join(s["health"]["issues"]) or "none"

    radios = "".join(
        f"<input type='radio' name='cv' id='cv-{vid}' class='vradio'{' checked' if i == 0 else ''}>"
        for i, (vid, _) in enumerate(_NAV))
    nav = "".join(f"<label class='cml-tab' for='cv-{vid}'>{_esc(label)}</label>" for vid, label in _NAV)
    view_css = "\n".join(
        f" #cv-{vid}:checked ~ main .view[data-view=\"{vid}\"]{{display:block}}\n"
        f" #cv-{vid}:checked ~ nav label[for=\"cv-{vid}\"]{{color:var(--green-800)}}\n"
        f" #cv-{vid}:checked ~ nav label[for=\"cv-{vid}\"]::after{{content:'';position:absolute;left:14px;"
        f"right:14px;bottom:-1px;height:2px;border-radius:999px;"
        f"background:linear-gradient(90deg,transparent,var(--gold-600) 18%,var(--gold-400) 50%,var(--gold-600) 82%,transparent);"
        f"box-shadow:0 1px 6px rgba(201,161,74,.5)}}"
        for vid, _ in _NAV)

    views = _overview(s) + _portfolio(s) + _decisions(s) + _regime(s) + _sharia(s) + _ops(s)

    halt_banner = ("<div class='k-halt-banner'>⛔ Kill switch engaged — the loop is frozen and no actions "
                   "will execute until a human resumes.</div>") if halted else ""

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Camel — Operator Dashboard</title>
<style>
 /* ===== Camel Design System tokens (offline; system-font fallbacks) ===== */
 :root {{
   --green-900:#0a2b25; --green-800:#0f3b34; --green-700:#16443a; --green-600:#1a3e2c; --green-300:#4f8276;
   --gold-700:#7a5a10; --gold-600:#a9842f; --gold-500:#c9a14a; --gold-400:#d8b96e; --gold-200:#ecd9a8;
   --sand-50:#faf7ee; --sand-100:#f5f1e6; --sand-200:#efe9da; --ink-800:#262626; --ink-500:#595959;
   --up-600:#1a7f37; --down-600:#c13c1e;
   --signal-green:#1a7f37; --signal-yellow:#9a6700; --signal-red:#cf222e; --signal-black:#24292f;
   --text-strong:#1b1b1b; --text-body:var(--ink-800); --text-muted:rgba(38,38,38,.55); --text-faint:rgba(38,38,38,.38);
   --surface-card:#fff; --line:rgba(38,38,38,.12); --line-strong:rgba(38,38,38,.22); --accent-wash:rgba(201,161,74,.16);
   --font-serif:'Iowan Old Style',Georgia,'Times New Roman',serif;
   --font-sans:system-ui,-apple-system,'Segoe UI',sans-serif;
   --font-mono:ui-monospace,'Cascadia Code','Segoe UI Mono',Consolas,monospace;
   --text-2xs:11px; --text-xs:12px; --text-sm:13px; --text-md:15px; --text-2xl:30px; --text-3xl:38px;
   --space-2:8px; --space-3:12px; --space-4:16px; --space-5:20px; --space-7:32px; --space-9:48px;
   --radius-sm:6px; --radius-md:8px; --radius-lg:12px; --radius-pill:999px;
   --shadow-sm:0 1px 3px rgba(15,59,52,.08); --shadow-header:0 2px 14px rgba(0,0,0,.15);
   --container:1100px; --grad-brand:linear-gradient(135deg,var(--green-800),var(--green-600));
   --grad-page:linear-gradient(160deg,var(--sand-200),var(--sand-100)); --transition:all .22s cubic-bezier(.22,.61,.36,1);
 }}
 *,*::before,*::after{{box-sizing:border-box}}
 body{{margin:0;font-family:var(--font-serif);font-size:16px;line-height:1.5;color:var(--text-body);
   background:var(--grad-page);-webkit-font-smoothing:antialiased}}
 .k-app{{max-width:var(--container);margin:0 auto;padding-bottom:var(--space-9)}}
 /* header */
 .k-header{{background:var(--grad-brand);color:var(--sand-100);padding:var(--space-5) var(--space-7);
   display:flex;align-items:center;justify-content:space-between;gap:var(--space-5);box-shadow:var(--shadow-header)}}
 .k-brand{{display:flex;align-items:center;gap:var(--space-4)}}
 .k-seal{{width:38px;height:38px;border-radius:50%;border:2px solid var(--gold-400);display:flex;align-items:center;
   justify-content:center;color:var(--gold-400);font-family:var(--font-serif);font-weight:700;font-size:18px;
   background:rgba(10,43,37,.4);flex:none}}
 .k-title{{font-family:var(--font-serif);font-weight:700;font-size:var(--text-2xl);letter-spacing:.01em;line-height:1}}
 .k-tag{{font-family:var(--font-sans);font-size:var(--text-2xs);color:rgba(245,241,230,.66);margin-top:5px;
   letter-spacing:.02em;max-width:70ch}}
 .k-kill{{font-family:var(--font-sans);font-weight:700;font-size:var(--text-sm);display:inline-flex;align-items:center;
   gap:8px;background:rgba(245,241,230,.08);color:var(--sand-100);border:1px solid rgba(245,241,230,.28);
   padding:9px 15px;border-radius:var(--radius-md);white-space:nowrap}}
 .k-kill--on{{background:var(--down-600);border-color:var(--down-600)}}
 /* status bar + nav */
 .k-statusbar{{display:flex;align-items:center;gap:var(--space-4);padding:var(--space-4) var(--space-7) 0;flex-wrap:wrap}}
 .cml-status{{font-family:var(--font-sans);font-weight:800;letter-spacing:.08em;color:#fff;padding:6px 15px;
   border-radius:var(--radius-md);display:inline-flex;align-items:center;gap:7px;font-size:var(--text-sm)}}
 .cml-status__dot{{width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,.85)}}
 .k-statusmeta{{font-family:var(--font-sans);font-size:var(--text-sm);color:var(--text-muted)}}
 .k-statusmeta b{{color:var(--text-body);font-weight:600}}
 nav{{display:flex;gap:2px;padding:var(--space-4) var(--space-7) 0;border-bottom:1px solid var(--line);
   flex-wrap:wrap;box-shadow:0 1px 0 rgba(201,161,74,.14)}}
 .vradio{{display:none}}
 .cml-tab{{font-family:var(--font-serif);font-weight:600;font-size:var(--text-sm);text-transform:uppercase;
   letter-spacing:.14em;color:rgba(15,59,52,.62);padding:13px 20px 14px;cursor:pointer;position:relative;
   border-radius:var(--radius-sm) var(--radius-sm) 0 0;user-select:none;transition:var(--transition)}}
 .cml-tab:hover{{color:var(--green-800);background:linear-gradient(180deg,transparent,var(--accent-wash))}}
 /* main + cards */
 main{{padding:var(--space-5) var(--space-7) 0}}
 .view{{display:none}}
{view_css}
 .k-stack{{display:flex;flex-direction:column;gap:var(--space-5)}}
 .k-kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:var(--space-3)}}
 .k-halt-banner{{display:flex;align-items:center;gap:var(--space-3);background:var(--signal-black);color:var(--sand-100);
   font-family:var(--font-sans);font-size:var(--text-sm);padding:var(--space-4) var(--space-5);
   border-radius:var(--radius-lg);margin-bottom:var(--space-5)}}
 .cml-card{{background:var(--surface-card);border:1px solid var(--line);border-radius:var(--radius-lg);
   padding:var(--space-5);box-shadow:var(--shadow-sm)}}
 .cml-card__head{{display:flex;align-items:center;gap:var(--space-2);margin-bottom:var(--space-2)}}
 .cml-card__title{{font-family:var(--font-serif);font-weight:700;font-size:var(--text-md);color:var(--green-800);margin:0}}
 .cml-card__hint{{font-family:var(--font-serif);font-size:var(--text-xs);color:var(--text-muted);line-height:1.5;margin:0 0 var(--space-3)}}
 .cml-stat{{background:var(--surface-card);border:1px solid var(--line);border-radius:var(--radius-lg);padding:var(--space-4) var(--space-5)}}
 .cml-stat__label{{font-family:var(--font-sans);font-size:var(--text-2xs);font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--text-muted)}}
 .cml-stat__value{{font-family:var(--font-mono);font-weight:700;font-variant-numeric:tabular-nums;font-size:var(--text-2xl);color:var(--ink-800);margin:5px 0 2px;line-height:1}}
 .cml-stat__sub{{font-family:var(--font-sans);font-size:var(--text-2xs);color:var(--text-muted)}}
 /* tables */
 .k-table{{border-collapse:collapse;width:100%;font-family:var(--font-sans);font-size:var(--text-sm)}}
 .k-table th{{font-size:var(--text-2xs);text-transform:uppercase;letter-spacing:.05em;color:var(--text-muted);
   font-weight:800;text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}}
 .k-table td{{padding:9px 10px;border-bottom:1px solid var(--line);color:var(--text-body);vertical-align:middle}}
 .k-table tbody tr:last-child td{{border-bottom:none}} .k-table tbody tr:hover{{background:rgba(15,59,52,.03)}}
 .k-empty{{color:var(--text-muted);font-style:italic;font-family:var(--font-serif);padding:6px 0}}
 .k-fig{{font-family:var(--font-mono);font-variant-numeric:tabular-nums;font-weight:600}}
 .k-gold{{color:var(--gold-700)}}
 .k-mono-sm{{font-family:var(--font-mono);font-size:var(--text-xs);color:var(--text-muted)}}
 .k-faint{{color:var(--text-faint)}}
 .k-code{{font-family:var(--font-mono);background:rgba(38,38,38,.06);padding:1px 6px;border-radius:4px;font-size:var(--text-xs);color:var(--gold-700)}}
 .cml-tick{{font-family:var(--font-mono);font-weight:700;color:var(--green-800);letter-spacing:.02em}}
 .cml-up{{color:var(--up-600)}} .cml-down{{color:var(--down-600)}}
 .cml-eyebrow{{font-family:var(--font-sans);font-size:var(--text-2xs);font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--text-muted)}}
 .cml-verdict{{font-family:var(--font-mono);font-weight:700;font-size:var(--text-sm);letter-spacing:.03em;display:inline-flex;align-items:center;gap:5px}}
 .cml-verdict--allow{{color:var(--up-600)}} .cml-verdict--block{{color:var(--down-600)}}
 .cml-badge{{font-family:var(--font-sans);font-weight:700;font-size:var(--text-2xs);letter-spacing:.04em;text-transform:uppercase;
   display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:var(--radius-pill);line-height:1.5}}
 .cml-badge--neutral{{background:rgba(38,38,38,.08);color:var(--ink-500)}}
 .cml-badge--gold{{background:var(--accent-wash);color:var(--gold-700)}}
 .cml-badge--green{{background:rgba(15,59,52,.10);color:var(--green-800)}}
 .cml-badge--up{{background:rgba(26,127,55,.12);color:var(--up-600)}}
 .cml-badge--down{{background:rgba(193,60,30,.12);color:var(--down-600)}}
 .cml-gate{{list-style:none;margin:0;padding:0}}
 .cml-gate__item{{display:flex;align-items:center;gap:var(--space-3);padding:9px 0;border-bottom:1px solid var(--line);font-family:var(--font-serif);font-size:var(--text-md);color:var(--text-body)}}
 .cml-gate__item:last-child{{border-bottom:none}}
 .cml-gate__mark{{width:20px;height:20px;flex:none;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;font-family:var(--font-sans);font-size:12px;font-weight:700}}
 .cml-gate__mark--ok{{background:rgba(26,127,55,.14);color:var(--up-600)}}
 .cml-gate__mark--bad{{background:rgba(193,60,30,.14);color:var(--down-600)}}
 .k-alloc{{display:inline-flex;align-items:center;gap:8px;font-family:var(--font-mono);font-size:var(--text-xs);color:var(--text-muted)}}
 .k-bar{{display:inline-block;width:64px;height:7px;background:rgba(38,38,38,.1);border-radius:4px;overflow:hidden}}
 .k-bar span{{display:block;height:100%;background:var(--gold-500)}}
 .k-regime-val{{font-family:var(--font-serif);font-weight:700;font-size:var(--text-3xl);color:var(--green-800);margin:3px 0;line-height:1.05}}
 .k-regime-conf{{font-family:var(--font-sans);font-size:var(--text-xs);color:var(--text-muted)}}
 .k-chips{{margin-top:var(--space-3);display:flex;flex-wrap:wrap;gap:8px}}
 .k-chip{{font-family:var(--font-mono);font-size:var(--text-2xs);background:rgba(15,59,52,.07);color:var(--green-800);padding:4px 10px;border-radius:var(--radius-pill)}}
 .k-footer{{text-align:center;font-family:var(--font-sans);font-size:var(--text-2xs);color:var(--text-faint);padding:var(--space-7) var(--space-7) 0}}
 @media (max-width:640px){{.k-tag{{display:none}} .k-header{{padding:var(--space-4) var(--space-5)}}}}
 @media (prefers-reduced-motion:reduce){{*{{transition-duration:.001ms!important}}}}
</style></head>
<body>
<div class="k-app">
<header class="k-header">
  <div class="k-brand">
    <span class="k-seal">C</span>
    <div>
      <div class="k-title">The Camel</div>
      <div class="k-tag">Read-only operator view · LLM proposes · Math tests · Guardrails decide · Humans approve · Autonomy earned</div>
    </div>
  </div>
  <span class="k-kill{' k-kill--on' if halted else ''}">{'⛔ HALTED' if halted else '◻ Kill switch: off'}</span>
</header>
{radios}
<div class="k-statusbar">
  <span class="cml-status" style="background:{status_var}"><span class="cml-status__dot"></span>{_esc('HALTED' if halted else status)}</span>
  <span class="k-statusmeta">Mode: <b>{_esc(mode)}</b> · {_esc(g['phase_label'])} · Kill switch: <b>{_esc(g['kill_switch'])}</b> · Issues: {_esc(issues)}</span>
</div>
<nav>{nav}</nav>
<main>{halt_banner}{views}</main>
<footer class="k-footer">Static read-only snapshot · no live fetch · no order entry · paper only. Not financial, legal, or Sharia advice.</footer>
</div>
</body></html>"""


def write_dashboard(dbs: CamelDbs, out_path: str, mode: str = "paper") -> str:
    htmls = build_dashboard_html(dbs, mode=mode)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(htmls)
    return out_path

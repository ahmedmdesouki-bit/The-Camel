# S15 — Paid tools & founder actions needed to cross "above the line"

> **What this is.** Everything that is **NOT code we can write for free** — it is either **paid** (a vendor
> subscription / API) or **pending on the founder** (a credential, a machine action, an explicit go-live
> decision). The S1–S14 build is complete and fail-safe *on paper*; this is the list that takes it **above
> the line** into real, scheduled, live operation. Each item names the code that is **already built and
> waiting** for it — so onboarding a dependency is "drop in the key / flip the switch," not "build it."

**The line:** below it = paper, offline, virtual money, 0 blockers (done). Above it = real data feeds, real
schedule, real money. Crossing it is deliberately the founder's act — no code here crosses it on its own.

---

## A. Paid vendors (money)

| Vendor | What it unlocks | Code already waiting | Priority |
|---|---|---|---|
| **EODHD** (Splits/Dividends + fundamentals) | Real ex-div dates / yield / payout / growth-streak; a 2nd fundamentals source to cross-check SEC | `strategies/dividend_growth.py`, `execution/corporate_actions.py` (the 4-stage NRA pipeline — has the *math*, needs the *feed*); `sharia/cross_check.py` (2nd source) | **High** — powers dividends + Sharia quorum |
| **Sharadar / Nasdaq Data Link** | Survivorship-free, point-in-time history for the *deepest* honest backtests | `edgelab/honest.py` (walk-forward/crisis), `edgelab/backtest.py` | Med — deepens Edge Lab |
| **Benzinga** (structured news) | High-quality event stream (vs. free GDELT/SEC-RSS) | `trader/events/intelligence.py`, `event_reactions` | Med |
| **Finnhub** (free tier — needs a key) | **Earnings calendar** + earnings surprise; event_reactions inputs | `guardrail/earnings_blackout.py` (the *rule* is built; inject the calendar), `trader/events/reactions.py` | Med |
| **Alpaca** (live trading + IEX websocket) | Real order placement (Phase 2) + the real-time streaming feed (S8.5) that replaces the sandbox stub | `broker/live.py` (gated `LiveBroker`, refuses without creds), `sandbox/runner.py` (injected feed) | Gated — Phase 2 |
| **IBKR** | Broader live execution (Phase 2) | `docs/CAMEL_BROKER_MATRIX.md` | Phase 2 |
| *(declined / later)* Polygon · Norgate · Quiver · Zoya · CRSP · RavenPack | Alternatives / enrichment | — | Deferred |

## B. Founder credentials (free, but you must provision)

| Credential | Enables | Code already waiting |
|---|---|---|
| `FRED_API_KEY` | Live macro ingestion (regime engine has real data) | `data/connectors/fred.py`, `data/ingest.py` (`macro_jobs`) |
| `BEA` / `EIA` keys | GDP / energy macro connectors | `data/connectors/bea.py`, `eia.py` |
| **Telegram bot token + founder chat id** | The one-tap **approve/veto** channel goes live | `governance/approval_channel.py` (inbound parse+dispatch — built), `alerts/` (outbound — built) |
| **Alpaca trade-only API key** (in env, never in repo) | `LiveBroker` can place orders once phase ≥ 1 | `broker/live.py` |
| Real **SEC / UA contact email** | SEC won't rate-limit/403 the live pulls | `data/connectors/base.py`, `sec_rss.py` headers |
| **OCR** (Tesseract install, or a paid OCR API) | Screenshot → text for Sahm confirmations | `broker/manual.py::parse_fill_text` (text→structured — built; needs image→text) |

## C. Founder machine + go-live actions (you, on your PC)

| Action | Detail | Reference |
|---|---|---|
| **Machine hardening** | Tailscale, BitLocker, secrets vault, off-box backups | `docs/CAMEL_MACHINE_HARDENING.md` |
| **Schedule the jobs** (Windows Task Scheduler) | `python -m data.ingest …` (populate DBs) · `python -m loop.jobs tick` (Edge-gated decision) · `python -m loop.jobs daily` / `weekly` (ops) | `data/ingest.py`, `loop/jobs.py` |
| **Build a ≥28-day track record** | Run the sandbox/paper loop; 0 breaches, ledger reconciles, a defensible Edge-Lab edge | `sandbox/runner.py`, `ops/live_readiness.py` |
| **The phase-flip** | Edit `config/limits.yaml` `phase: 0 → 1` + `live_enabled` — deliberately, with real (tiny) capital | `config/limits.yaml`, `guardrail/constitution.py` |
| **Fund the account** | ~$126 + $100/mo on Sahm (whole shares) → the $10K "Camel Fund" target | — |

---

## Not S15 (free code we can still write — tracked, not blocked)
These are neither paid nor founder-gated — they are free-pattern connector/code work on the established
framework, available whenever we want to extend coverage (do NOT belong above the line):
- More **free connectors**: GPR/EPU geopolitical indices, Kenneth-French factors, CFTC COT, an OFAC SDN
  sanctions screen (needs a small sanctions table), congress/senate disclosures.
- The **physical module reorg** (S14) — ✅ **DONE 2026-06-08** (the Trader Camel packages now live under
  `trader/`; 603 tests still green). No longer outstanding.

## Bottom line
Everything below the line is **done, tested (603 green), and fail-safe**. S15 is the shopping list +
switch-flips to go above it — and every one of those plugs into code that is already built and waiting.
Going live remains the founder's explicit act.

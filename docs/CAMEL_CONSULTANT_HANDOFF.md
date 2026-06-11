# The Camel — Project Description & Consultant Handoff

> **Purpose of this document.** A self-contained briefing for an external reviewer (architecture / quant /
> Sharia-finance / security) to understand what The Camel is, how it is built, what is and isn't done, and
> where the founder most wants a critical eye **before any real money is ever at risk**. It synthesizes the
> internal docs; pointers to the canonical source for each topic are given throughout.
>
> **Status at a glance:** Phase 0 (paper only) · build S1–S17 complete · **763 automated tests green** · live
> free data feeds (Alpaca paper prices + FRED macro) · first real *paper* fill recorded · running on a daily
> Windows scheduled task. **No real capital has ever been at risk, and no code path can put it there** — going
> live is a deliberate, gated founder action.
>
> Last updated: 2026-06-11 · Repo: <https://github.com/ahmedmdesouki-bit/The-Camel> · Local canonical: `C:\camel`

---

## 1. Executive summary

The Camel is a **guardrailed, Sharia-compliant autonomous operator** that runs a continuous
*Observe → Thesis → Choose → Act → Measure → Learn* loop. Its defining principle is an **inversion of trust**:
the reasoning/proposing layer only *proposes*; a deterministic **Constitution it cannot edit**, an **Edge-Proof
evidence gate**, a **Budget Kernel**, append-only **audit logs**, a **kill switch**, and **human approval gates**
*decide* what actually happens. The slogan that governs every design trade-off:

> **Safety first. Evidence second. Autonomy last.**
> LLM proposes · Math tests · Guardrails decide · Humans approve what's risky · **Autonomy is earned, not granted.**

It has two arms: **Trader Camel** (Sharia-compliant markets — the mature arm) and **Entrepreneur Camel**
(Sharia-compliant AI products — an engine only, not yet wired to a live product). This handoff focuses on the
Trader arm, which is where capital risk lives.

**The founder** is a Riyadh-based operator who works full-time in travel-tech; the real account is a Saudi
broker (Sahm) holding US-listed Sharia ETFs. The Camel is being built to eventually manage a small (~$10k)
"Camel Fund" — but only after it earns trust through a paper track record.

**The ask for the consultant** is in §13. In short: *stress-test the safety model and the go-live readiness;
tell us what would make this dangerous with real money, and what's missing before that line is crossed.*

---

## 2. The core idea (and what it is NOT)

**What it is:** a system whose *guardrails* are the product. The intelligence layer is treated as fallible and
possibly adversarial; the value is in a deterministic constitution, an evidence gate, hard risk limits, and
human approval — all of which the agent process **cannot modify**. Autonomy expands only as a paper track
record accumulates.

**What it is NOT:** a stock-picking chatbot. It is explicitly designed to be *excellent at rejecting weak ideas,
proving the rare strong ones, compounding patiently, and never moving real money it wasn't told to.*

**The priority hierarchy — never inverted (enforced in code + review):**

```
1. Sharia compliance   2. Capital preservation   3. System integrity   4. Evidence quality
5. Learning speed      6. Return generation       7. Autonomy expansion
```

> ⚠️ **Important nuance for a reviewer:** *today the "proposer" is a set of deterministic, rule-based
> strategies* (DCA, momentum, mean-reversion, ETF-rotation, dividend-growth), **not** an LLM. The LLM-desk
> layer is designed but **dormant** (it needs paid API spend; see §9, S17.8). This is deliberate: the guardrails
> are being proven against simple, auditable proposers first. The trust-inversion machinery is fully built so
> that when an LLM proposer is switched on, it is gated identically.

Canonical: `CLAUDE.md` (operating manual), `docs/CAMEL_BRIEF.md` (why/who), `docs/CAMEL_CONSTITUTION.md` (rules).

---

## 3. Current status

**The whole build S1–S17 is implemented, tested, fail-safe, and on `main`.** Highlights:

- **Safety core (S1–S6.6):** the Constitution, Sharia gate, paper broker + hash-chain ledger, Budget Kernel,
  freshness/quality gates, config-immutability *proof*, kill switch inside `evaluate`, position accounting,
  ops/monitoring, beginner mode.
- **Engine (S7–S12.5):** Entrepreneur product gate; the Data Intelligence Backbone (12+ provenance-stamped
  connectors); the Knowledge Graph + 10-state Regime Engine + verified AAOIFI Sharia cross-check; the **17-check
  Edge-Proof Engine**; the assembled operator loop; the Strategy Registry + Portfolio Engine + Learning;
  the Edge Lab (backtests) + realistic-paper executor + ⭐ Sandbox; the dormant Research-Desk framework.
- **Operational activation (S16):** the loop now does *durable* work — real paper fills + a graded `runs` row,
  Measure→Learn closed, governed reduce-only exits, the **No-Edge→DCA** path, the data-quality gate, a DCA
  cadence guard. **The first real paper fill is recorded; the ≥28-run readiness clock has started.**
- **The Workforce (S17):** the one loop decomposed into named **desks** (SCOUT/HERALD/ORACLE/MUFTI/QUANT/
  STEWARD/CONDUCTOR), an **Opportunity Board** (ranked, reasoned, governed proposals), a **Kitchen** cockpit,
  a **Supervisor** with a token/API **cost cap**, a DAG scheduler, a proposal self-check, memory consolidation,
  and a read-only **camel-coach**.

**Live operational facts (paper):** the `$10k` paper book is seeded; the data taps are on (Alpaca paper IEX
prices + FRED macro); the regime classifies **RECOVERY** on real Fed data; the Edge Lab honestly returns
**NO_EDGE** for the current ETF universe, so the system **DCAs into the compliant core** rather than inventing
alpha. A daily Windows scheduled task runs the governed cycle on weekday nights.

Canonical: `docs/CAMEL_ROADMAP.md` (full sprint plan + definition of done), `docs/CAMEL_CHANGELOG.md` (history).

---

## 4. Architecture overview

**The governed loop (§4 — what one tick does):**

```
Observe (macro regime)
  → Generate opportunities (strategies propose)
  → Opportunity Router            (Trader / Entrepreneur / Research / System / WAIT — leans to Wait)
  → Edge Proof  (17 checks)       (no buy proceeds without a passing EdgeReport)
  → Constitution                  (Sharia #1, risk limits, kill switch — the hard wall)
  → Budget Kernel                 (per-action + rolling spend caps)
  → Human Approval gate           (phase-gated; withholds by default at phase ≥ 1)
  → Act                           (paper broker → orders + ledger + positions, one transaction)
  → Measure → Learn               (resolve round-trips, update strategy base-rates, propose-only changes)
```

The load-bearing invariant (tested): **a buy with no passing EdgeReport is rejected by the *assembled* loop**,
because every consequential action routes through the allocator (Edge + Constitution), never the Constitution
directly. Order of authority is preserved end-to-end.

**Seven-database SQLite architecture** (Phase 0), each domain isolated, all carrying **point-in-time
timestamps** (`event_date · reported_at · ingested_at · known_at`) so backtests cannot look ahead:

| DB | Content |
|---|---|
| `camel_market.db` | prices, dividends, splits |
| `camel_macro.db` | rates, yield curve, VIX, credit spreads, regime history |
| `camel_fundamentals.db` | revenue, margins, debt, cash (for the AAOIFI screen) |
| `camel_news.db` | structured event objects (never raw text to the reasoning layer) |
| `camel_sharia.db` | whitelist (versioned), sharia status, sanctions |
| `camel_portfolio.db` | orders, positions, hash-chain ledger, runs |
| `camel_learning.db` | decisions, outcomes, base-rates, desk runs, proposals |

Canonical: `docs/CAMEL_ARCHITECTURE.md` (layered module map), `docs/CAMEL_DATA_CONTRACTS.md` (schemas + PIT).

---

## 5. The safety model (the heart of the review)

These are **non-negotiable, code-enforced** invariants. Limits live in `config/limits.yaml`, which the agent
process is **provably unable to write** (a startup config-immutability test asserts an agent-initiated write
raises and is logged — Constitution rule #7 is proven, not asserted).

1. **Sharia gate is a hard wall.** Only whitelisted, compliant, non-frozen instruments are tradeable. No
   leverage, derivatives, shorting, margin, or crypto-derivatives — ever. (§7.)
2. **No position without a written invalidation** (invalidation + profit-take + time-stop).
3. **Withdrawals are forbidden** — the live broker key must be trade-only, withdrawals disabled.
4. **Live money needs a human approval gate** until later phases; **Phase 0 is paper only.**
5. **Everything is logged** — append-only ledger with a SHA-256 hash chain; limits are founder-owned config.
6. **No trade without a passing EdgeReport** — the 17-check Edge Proof (pre-registered thresholds,
   multiple-testing penalty, signal-decay, regime conditioning, Sharia fail-safe, model-disagreement→human,
   shadow/enforcing modes). The one deliberate exception: **edge-exempt DCA into the already-Sharia-screened
   compliant core** (the benchmark itself, not an alpha bet) — *alpha trades still require proof*.
7. **Kill switch is checked inside `Constitution.evaluate()`** — it gates *every* consequential action, not just
   the loop start; there is no path around it.
8. **Cannot act on stale or single-source data;** **cannot act unless broker/account state reconciles.**
9. **Phase gates:** 0 = paper · 1 = micro-live (every order human-approved) · 2+ = bounded autonomy. The phase
   has a *single* founder-owned source (`config/limits.yaml`); the agent cannot flip it.
10. **Budget Kernel** — per-action envelope + rolling daily/weekly/monthly spend caps, always present and
    binding (never silently skipped).

Canonical & authoritative: `guardrail/constitution.py` + `config/limits.yaml`. Prose: `docs/CAMEL_CONSTITUTION.md`.
Adversarial test suite (config-edit, frozen-symbol, stale-data, duplicate-order, permission-bypass,
prompt-injection-override, no-EdgeProof-signal, etc.) is part of the 763.

---

## 6. Sharia compliance approach

- **In-house verified AAOIFI screen** (`sharia/aaoifi.py`): debt ÷ 12-mo-avg market cap ≤ 30%; (cash + deposits
  + interest-bearing investments) ÷ 12-mo-avg market cap ≤ 30%; (cash + deposits + receivables) ÷ total assets
  ≤ 67%; non-compliant revenue ≤ 5%; an 11-sector business-activity screen; a "doubtful" band; a purification
  ratio.
- **Multi-state cross-check** (`sharia/cross_check.py`): `pass / fail / doubtful / frozen / pending_review`,
  with a **fail-safe quorum** (a single source can *fail* a name but not *clear* it) and **disagreement → freeze**.
  Authority stack: local board > AAOIFI > founder-tighten-only > agent-never.
- **The current universe** is two issuer-Sharia-board-governed ETFs (**SPUS**, **HLAL**); the founder's
  attestation rests on the issuers' screening. **Individual equities** will only become tradeable once
  fundamentals data exists to run the in-house screen on them (a paid-data dependency).
- **OFAC sanctions screen** (`sharia/sanctions.py`) guards universe seeding — a sanctioned entity is refused.
- A **quarterly re-screen** schedule surfaces names due for review; drift protection is fail-safe (any
  non-clear outcome freezes the name → close-only + auto-exit).

> **Review note:** for the consultant with Sharia-finance expertise — please scrutinize the ratio thresholds,
> the 12-mo-avg market-cap basis, the doubtful-band handling, and whether issuer attestation for the ETFs is
> a sufficient basis for the founder's purposes.

---

## 7. Data & evidence (and an honest result)

- **Free feeds live now:** **Alpaca** (paper IEX daily bars, US stocks/ETFs since 2016) for prices; **FRED**
  for macro (Fed funds, 2y/10y yields, VIX, HY credit spreads, the SAR/USD peg). Connectors use stdlib `urllib`
  (zero-dependency, injectable transport, no live web in tests).
- **Point-in-time discipline** everywhere (four timestamps) so backtests are honest; vintage-aware reads.
- **Provenance**: no decision-relevant record is stored without source/url/hash/parser-version/quality-score;
  a `source_documents` audit row per fetch; raw text is sanitized to structured events before reaching the
  reasoning layer (injection-hardened).
- **The honest result so far:** the Edge Lab (cost-aware, two-engine cross-check, beats-DCA test) returns
  **NO_EDGE** for SPUS/HLAL — a trend strategy loses to buy-and-hold after costs. The system's correct response
  is **DCA into the compliant core**, *not* to manufacture a signal. This is the intended behavior and the
  clearest demonstration of the philosophy.

> **Known data limitations (for review):** (a) **single price source** today (Alpaca) — no multi-source quorum
> yet; (b) the production paper broker fills at **last close** (`simulated_unrealistic`); a realistic executor
> (spread/slippage/partial fills) exists but is currently exercised in the **Sandbox**, not the production tick;
> (c) the **GPR** (geopolitical-risk) and **OFAC** connectors are built + fixture-tested but their *live
> endpoints are unvalidated* (like any connector before first real use); (d) individual-equity fundamentals
> (for the AAOIFI screen) require a paid feed.

Canonical: `docs/CAMEL_DATA_SOURCES.md`, `docs/CAMEL_DATA_CONTRACTS.md`.

---

## 8. The operator workforce (S17)

The single governed loop is decomposed into named, single-job **desks** — SCOUT (data), HERALD (news), ORACLE
(regime), MUFTI (Sharia), QUANT (edge), STEWARD (portfolio), CONDUCTOR (decision). Evidence desks can *only*
write evidence (no act/execute method exists on them — a test pins this); only the CONDUCTOR can cause a buy,
and only through the full gated path. Around them:

- **Opportunity Board** — a ranked, reasoned, *governed* proposal per name with its full reason chain; Sharia
  is a hard wall (a non-compliant name is `avoid`, never a buy); no-edge → `dca`; the founder approves.
- **Kitchen** — a watch-and-control cockpit (founder-only commands: pause/resume/run a desk, approve/veto a
  proposal) over the existing command channel.
- **Supervisor** — auto-restart + quarantine for flaky desks, and a **hard token/API cost cap** (the
  "runaway-bill" guardrail that makes any future LLM desks safe to enable).
- **Proposal self-check / DAG scheduler / memory consolidation** — coherence invariants, dependency-ordered
  runs, and operational-memory rollups.

Canonical: `docs/CAMEL_S17_WORKFORCE.md`.

---

## 9. Deployment topology & operations

- **Brain / window / bridge split.** The **Python brain** runs on the founder's Windows PC (canonical local
  repo `C:\camel`). A read-only **Next.js "window"** is deployed on Vercel (`the-camel-five.vercel.app`),
  friends-only (magic-link + double allowlist, fail-closed). **Supabase** is the bridge: the brain *publishes*
  state; the window *reads* it. The Supabase service-role key lives brain-side only, never in Vercel or the repo.
- **The clock.** Two Windows scheduled tasks: **Camel Brain Daily** (weekdays 23:45, after US close in Riyadh
  time → one governed paper cycle) and **Camel Weekly Safety** (Sundays → kill-switch self-test + backup +
  reconcile). Currently **run-when-logged-on** (the PC must be awake + logged in); converting to headless is
  the next founder-machine task.
- **Secrets** live only in a git-ignored brain-side `.env` (and, for hardening, Windows Credential Manager).
  All keys in use today are **paper / read-only / regenerable**.

---

## 10. How to run / verify it (for the reviewer)

```bash
git clone https://github.com/ahmedmdesouki-bit/The-Camel.git
cd The-Camel
python demo.py        # seeds 7 SQLite DBs, drives ONE fully-governed tick, writes a read-only HTML dashboard
                      # fully offline, paper-only, no credentials
pytest -q             # expect 763 passed
```

`demo.py` proves the spine offline: a proven-edge name passes every gate and fills with realistic costs; a
frozen/non-compliant name is held out by the Sharia gate (and the dashboard *shows the rejection — the
rejections are the point*); an inverted-curve macro flips the router to **Wait**. The brain's daily cycle is
`scripts/run-brain.ps1` (Windows). The read-only Q&A tool is `python -m founder_tools.coach "status"`.

> **Note:** the repo path on the founder's machine exceeds Windows `MAX_PATH`; it has been relocated to the
> short path `C:\camel` so tests + the scheduler run without a virtual-drive workaround. A reviewer cloning to
> any normal path will not hit this.

---

## 11. What is NOT done / known limitations & risks (candid)

A self-run adversarial audit (2026-06-09) framed honest distances; S16 then closed the operational gaps. As of
today:

- **Track record is ~0 days.** The readiness gate wants **≥28 days** of clean paper/sandbox operation; the
  clock just started. *Nothing about the system is "proven" in live behavior yet.*
- **No proven edge yet.** The current ETF universe yields NO_EDGE → the system DCAs. That is honest, but it
  means the alpha machinery is unexercised by a *real* edge in production.
- **Deterministic proposers today.** The LLM-desk layer (S17.8) is dormant (needs paid API spend); the
  cost-cap + evidence-only contract are built to gate it when enabled.
- **Production fills are last-close** (`simulated_unrealistic`); the realistic-fill executor lives in the
  Sandbox. The production track record is therefore slightly optimistic on execution.
- **Single price source; GPR/OFAC live endpoints unvalidated; equity fundamentals need paid data** (§7).
- **Entrepreneur arm is an engine only** — gated, but not wired to a real product, Stripe, or deploy.
- **Run-when-logged-on** — the daily cycle only fires while the PC is awake and logged in (headless is next).

None of these are *safety* overstatements — every guardrail is a tested hard wall, and no code path risks real
money. They are *progress/maturity* caveats a reviewer should weigh.

---

## 12. What's left to go live (all paid or founder-gated)

| Item | Type |
|---|---|
| Run the brain **headless** (run-whether-logged-on; needs admin + stored creds) | Founder machine — *next* |
| A **≥28-day** clean paper/sandbox track record | Time (accruing now) |
| **Paid feeds**: EODHD · Sharadar (survivorship-free backtests) · Benzinga · Finnhub · live Alpaca · IBKR | Paid |
| **Machine hardening**: BitLocker, Tailscale, dedicated OS user, UPS, MFA | Founder machine |
| The **phase-flip** in `config/limits.yaml` → real (tiny) capital | **Founder's explicit act** |

**No free code remains.** Canonical: `docs/CAMEL_S15_PAID_AND_FOUNDER.md`, `docs/CAMEL_LIVE_READINESS.md`.

---

## 13. ⭐ Specific questions for the consultant

1. **Safety model.** Is the trust-inversion *complete*? Can you find any path — config write, state machine,
   broker call, prompt injection, data poisoning — by which the agent could move real money, change a limit, or
   trade a non-compliant/sanctioned name? (Start at `guardrail/constitution.py` + `capital/allocator.py` +
   `loop/assembled.py`; the adversarial tests are in `tests/`.)
2. **Go-live readiness.** Beyond the ≥28-day record, what *must* be true before the phase-flip? What would you
   add to the live-readiness checklist? Is "every order human-approved" at Phase 1 sufficient?
3. **Evidence / Edge Proof.** Are the 17 checks the right ones? Is the multiple-testing penalty + signal-decay
   + beats-DCA bar rigorous enough to avoid false positives on a small account? Is last-close paper fill an
   acceptable basis for the track record, or must the realistic executor drive production first?
4. **Sharia methodology.** (§6.) Are the AAOIFI thresholds, the doubtful-band handling, and ETF issuer
   attestation appropriate? Where would a stricter board disagree?
5. **Data integrity.** Is single-source price data acceptable for a paper track record? What is the minimum
   quorum / cross-check you'd require before live? How would you harden against a bad vintage / silent feed gap?
6. **Risk sizing.** For a real ~$10k book via a Saudi broker (whole-share, fees), are the position caps, cash
   buffer, rolling velocity stops, and DCA cadence sensible? What's the first thing you'd tighten?
7. **The honest NO_EDGE result.** Is "DCA into the compliant core when there's no edge" the right default, or
   would you argue for pure cash until an edge appears?
8. **Operational risk.** Brain-on-a-home-PC, run-when-logged-on, Supabase bridge — what's the weakest link?

Candor is welcome; the founder would rather hear "don't go live until X" now than discover X with real money.

---

## 14. Where to look (repo map for a reviewer)

| To review… | Read |
|---|---|
| The rules (authoritative) | `guardrail/constitution.py` + `config/limits.yaml` |
| The assembled loop + the no-edge-no-trade invariant | `loop/assembled.py`, `loop/driver.py`, `loop/jobs.py` |
| The Edge Proof engine | `trader/engine/edge_proof.py` |
| Sharia screen + cross-check + sanctions | `sharia/aaoifi.py`, `sharia/cross_check.py`, `sharia/sanctions.py` |
| Regime engine | `trader/regime/` |
| Strategies (deterministic proposers) | `trader/strategies/` |
| Edge Lab + realistic executor + Sandbox | `trader/edgelab/`, `trader/execution/`, `trader/sandbox/` |
| The operator workforce | `research/`, `loop/opportunity_board.py` |
| Tests (incl. adversarial) | `tests/` |
| Operating manual / full plan / go-live | `CLAUDE.md`, `docs/CAMEL_ROADMAP.md`, `docs/CAMEL_LIVE_READINESS.md` |

**Source-of-truth rule:** a fact has one home; **code beats docs** — `guardrail/constitution.py` +
`config/limits.yaml` are authoritative. The full documentation index is `docs/README.md`.

---

*The Camel is patient capital, governed by evidence. This document is a description of a paper-stage system; it
is not financial or Sharia advice, and nothing in the codebase places real capital at risk without a deliberate,
founder-owned act.*

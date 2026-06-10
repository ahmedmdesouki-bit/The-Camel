# CAMEL S17 — THE WORKFORCE (Desks · Supervisor · Scheduler · Kitchen)

> **Canonical plan for the "named workforce" upgrade.** Decomposes The Camel's one governed loop into a
> roster of named, single-job **desks**, puts a **supervisor** over them, a **scheduler** between them, and
> a live **Kitchen** cockpit over the whole thing — turning the operator from a passive paper loop into an
> active, watchable, self-healing research-and-recommendation engine that surfaces *governed, evidence-backed
> proposals* ("where to put the money") for the founder to approve.
> **Status (2026-06-10): FIRST SLICE BUILT — S17.1 + S17.6 + S17.7 DONE & QA-reviewed (700 tests green).**
> Derived from the founder's review of the "6-Level AI-agent" framework (Professor Glitch) mapped onto The Camel.
>
> **✅ S17.1 desks** (`research/workforce.py` + `research/roster.py`: the 7-desk roster, no-act invariant
> enforced, `desk_runs` audit, run-isolation). **✅ S17.6 Opportunity Board** (`loop/opportunity_board.py`:
> ranked/reasoned governed proposals, Sharia-#1 hard wall, no-edge→DCA, proposes-only). **✅ S17.7 Kitchen**
> (brain: `governance/desk_control.py` pause/resume, founder-only Kitchen commands in `ops/command_poller`,
> desks+board folded into the published `system_state` snapshot; web: a Kitchen panel on the dashboard —
> `web/components/Kitchen.tsx` — watch desks + steer the board via the existing founder-only command channel).
> An adversarial review confirmed the trust-inversion holds (evidence desks cannot act; the tick never reads
> the board; controls are founder-only fail-closed) — **safe-to-commit, no guardrail weakened.**
> **⏳ Remaining sub-sprints: S17.2 (supervisor + cost cap), S17.3 (scheduler/DAG), S17.4 (proposal
> self-check), S17.5 (memory consolidate), S17.8 (LLM desks).**
>
> **WEB DEPLOY (founder-driven, ~5 min) — the Kitchen *panel* code is in `web/` but not yet live on Vercel.**
> It rides the EXISTING `system_state` + `commands` Supabase tables (no new tables, no schema change). To go
> live: (1) on the brain PC run a workforce cycle + board build + publish so the snapshot carries `desks`/`board`
> (`python -m research.workforce cycle` → `python -m loop.opportunity_board` → `python -m ops.publish_state`),
> (2) push to GitHub (Vercel auto-deploys the new Kitchen panel + `/api/command` types). No env-var change needed.
> Until data flows (Alpaca+FRED keys) the board is empty and the desks show 'empty' — expected.

---

## 0. The one truth that frames everything

The desks are the **brain**; data is the **blood**. Today the data tap is **OFF** (no price feed until a free
Alpaca paper key; no macro until a free FRED key — Stooq is bot-blocked). Every desk below will RUN without
data, but it can only *find opportunities* once data flows. So:

- This whole initiative is a **processing / observability / robustness** upgrade. It makes the operator
  organized, watchable, self-restarting, and clear about *why* it proposes what it proposes.
- It is **not, by itself, an alpha upgrade.** Alpha comes from real data + the Edge-Proof discipline we already
  have. The Edge Lab stays brutally honest: it will often answer **"no edge → DCA,"** which is the system
  protecting capital, not failing.
- **"Where to put my money"** is delivered as **ranked, reasoned, governed proposals the founder approves** —
  never blind auto-trading, never licensed financial advice. The Constitution keeps the human as the decider.

**The single highest-leverage founder action remains the two free signups (~30 min).** Build the workforce so
it's ready the instant data lands — but the keys are the unlock.

---

## 1. How the desks map onto the existing system

The desks are **the existing §4 loop, decomposed and named** — not new logic bolted on. Each wraps an engine
we already built and emits a structured result (and, where it's an analyst, an `EvidenceObject` against the
S12.5 contract that already exists in `research/`).

| Desk | One job | §4 loop stage | Wraps (already built) | Kind |
|---|---|---|---|---|
| **SCOUT** | find data: prices · macro · filings | Observe (ingest) | `data/ingest`, Alpaca/FRED/SEC/Stooq connectors | operator (writes data DBs only) |
| **HERALD** | gather + sanitize news/events | Observe (news) | `trader/events`, news connectors | evidence |
| **ORACLE** | macro regime + SAR-peg read | Observe (macro) | `trader/regime`, `MacroDesk` (exists) | evidence |
| **MUFTI** | Sharia screen + drift→freeze | Observe (compliance, priority #1) | `sharia/`, `ShariaDesk` (exists) | evidence (+ may freeze whitelist) |
| **QUANT** | the edge — 17-check proof + Edge-Lab verdict | Choose (Edge Proof) | `trader/engine/edge_proof`, `trader/edgelab` | evidence |
| **STEWARD** | portfolio — positions · P&L · exits · base-rates | Measure + Act(exits) | `broker`, `trader/portfolios`, `learning`, `trader/execution/exits` | operator (governed exits only) |
| **CONDUCTOR** | assemble all evidence → ranked governed proposal → founder approval → Act | Choose → Act | `loop/assembled`, `capital/allocator`, `operator_os/opportunity_router`, `governance/approval` | operator (the ONLY desk that can cause a buy) |
| *(future)* **SCRIBE** | the Entrepreneur arm — pick/scope an AI product | Choose (Entrepreneur path) | `entrepreneur/` | operator (code-gen-only autonomy) |

**The trust-inversion is unchanged and must stay unchanged.** Evidence desks (HERALD/ORACLE/MUFTI/QUANT) keep
`AnalystDesk`'s guarantee: **no `act`/`execute`/`trade` method exists on them at all** — they only write
`EvidenceObject`s. SCOUT only writes data tables. STEWARD's exits and CONDUCTOR's buys still route through the
full stack (Edge Proof → Constitution → Budget → Approval → Broker). **No desk gets a path around a gate.**

---

## 2. The sub-sprints (the menu)

Each is independently pickable; dependencies are noted. Sizes are rough (S ≈ 1–2 focused build+QA batches,
M ≈ 3–4, L ≈ 5+). Every sprint ends green on the full suite and gets an adversarial QA pass before commit.

### S17.1 — Desk framework + roster  ·  Level 4  ·  size **M**  ·  deps: none
**Goal:** generalize the dormant `research/` framework into the workforce abstraction and implement all 7 desks
as thin wrappers over existing engines.
- **Deliverables:** `research/workforce.py` (a `Desk` protocol: `run(ctx) -> DeskResult{status, outputs,
  evidence, metrics}`; an evidence-desk base that *cannot act*, reusing `AnalystDesk`; an operator-desk base
  for SCOUT/STEWARD/CONDUCTOR); the 7 desk classes (`research/desks/*.py`); a `DeskRegistry`; a `desk_runs`
  audit table (db/learning or a new ops DB); CLI `python -m research.workforce run <desk>`.
- **Design:** desks are deterministic now (LLM bodies are S17.8). Each desk reads governed DBs + an injected
  run-context and returns a `DeskResult`. EvidenceObjects continue to flow only into `research_evidence`.
- **Guardrails:** add a test proving no evidence desk exposes act/execute/trade; SCOUT writes only `prices`/
  `macro_observations`/`news_events`; CONDUCTOR is the sole trade path and still goes through the allocator.
- **Data-gating:** desks emit thin output until data flows; framework + audit are fully testable with seeded DBs.
- **Gate / DoD:** each of the 7 desks runs standalone, returns a valid `DeskResult`, writes a `desk_runs` row;
  the no-act invariant is test-proven; full suite green.
- **Tests:** per-desk output shape; no-act invariant; SCOUT writes only data; CONDUCTOR still rejects a no-edge buy.

### S17.2 — Supervisor + hard cost cap  ·  Level 5 (Supervisor)  ·  size **M**  ·  deps: S17.1
**Goal:** run the roster reliably and un-babysat, with a hard ceiling on spend (the "runaway API bill" guardrail).
- **Deliverables:** `ops/supervisor.py` — runs a desk set with per-desk isolation (one failure never aborts the
  rest), **retry-with-backoff + quarantine** after N failures, a per-desk **heartbeat/health** record, and a
  **token/API-cost budget cap**: extend `capital/budget_kernel` with a cost ledger so the supervisor refuses to
  run further desks once the daily cost cap (founder-owned in `config/limits.yaml`) is hit. Reuses the kill
  switch + `ops/deadman`. Writes `desk_runs` + `op_log`.
- **Guardrails:** the cost cap is a NEW guardrail (only-tightens, founder-owned); the supervisor cannot disable
  the kill switch; a quarantined desk stays quarantined until a human clears it.
- **Data-gating:** none — fully testable with stub desks (a crashing desk; a cost-overrun desk).
- **Gate / DoD:** a crashing desk is retried then quarantined without aborting the cycle; exceeding the cost cap
  halts further desk runs and fires the founder alert; heartbeats recorded; full suite green.
- **Tests:** crash→retry→quarantine; cost-cap halt; kill-switch still halts the supervisor; heartbeat written.

### S17.3 — Scheduler + message-passing (the desk DAG)  ·  Level 5 (Scheduler)  ·  size **S**  ·  deps: S17.1, S17.2
**Goal:** desks run on the right cadence and feed each other deterministically (SCOUT→ORACLE/MUFTI→QUANT→CONDUCTOR).
- **Deliverables:** a desk **manifest** (cadence + dependency edges) in `config/`; `research/workforce.cycle`
  that topologically runs the DAG passing each desk's `DeskResult` as context to its dependents; wire into
  `scripts/run-brain.ps1` + a Task-Scheduler entry. Message-passing is a shared run-context object — a
  deterministic pipeline, **not** agent chit-chat (avoids the "cap the chatter" failure mode).
- **Guardrails:** no new trade path; the DAG only orders existing governed steps.
- **Gate / DoD:** `python -m research.workforce cycle` runs all desks in dependency order with context threaded;
  cadence honored; tested on seeded data.
- **Tests:** DAG order; context handoff (a downstream desk sees an upstream evidence object); cadence filter.

### S17.4 — Body+Loop hardening (proposal self-check)  ·  Level 2  ·  size **S**  ·  deps: S17.1
**Goal:** before the CONDUCTOR emits any proposal, it re-verifies the evidence is fresh, quorum-backed, and
Sharia-clear — act·check·**retry** at the decision boundary.
- **Deliverables:** a `verify()` step in the CONDUCTOR that re-runs the freshness gate (`data/freshness`) +
  source-quorum (≥2) + latest Sharia status on every input evidence object; a stale/thin/uncleared input
  **drops the candidate** with a logged reason; a bounded retry that re-pulls the latest evidence once.
- **Guardrails:** strengthens "Camel cannot act on stale or single-source data" (Constitution rule #8) at the
  proposal layer; never loosens it.
- **Gate / DoD:** a proposal built on a stale or single-source evidence object is refused by the self-check;
  tested.
- **Tests:** stale evidence → dropped; single-source → dropped; fresh+quorum+compliant → passes.

### S17.5 — Memory hardening (consolidate + patterns store)  ·  Level 3  ·  size **S**  ·  deps: none
**Goal:** "goldfish → employee" hygiene + a long-term pattern store the desks read.
- **Deliverables:** `learning/consolidate.py` — merge duplicate learning-ledger entries, drop stale/never-
  resolved notes (without ever dropping a *resolved* outcome), on a weekly cadence; a read-only **patterns**
  view the desks consult (regime→strategy affinity from `learning/regime_matcher`, `event_reactions` priors);
  a "what the system remembers" block for the dashboard snapshot.
- **Guardrails:** consolidation is propose-safe (it compacts memory, never edits the Constitution, limits, or a
  resolved P&L outcome); patterns are read-only priors.
- **Gate / DoD:** consolidation merges dupes + drops stale while preserving every resolved round-trip; desks can
  read the patterns store; tested.
- **Tests:** dup-merge preserves resolved outcomes; stale-drop; pattern read.

### S17.6 — The Opportunity Board (the "where to put my money" output)  ·  size **M**  ·  deps: S17.1 (+ richer with S17.3)
**Goal:** the CONDUCTOR turns the desks' evidence into a **ranked, reasoned proposal board** — the founder-facing
"insight," governed and explainable.
- **Deliverables:** `loop/opportunity_board.py` — for each candidate symbol, assemble the full chain (ORACLE
  regime · MUFTI Sharia status · QUANT Edge verdict + base-rate · STEWARD portfolio fit/concentration ·
  proposed action + invalidation + confidence), rank by a transparent score, and persist to a `proposals`
  table (status: proposed/approved/vetoed/expired). Each row carries its **reason chain** (the evidence_ids).
  Honest by construction: when QUANT finds no edge, the recommended action is **DCA into the compliant core**,
  flagged as a success state.
- **Guardrails:** the board PROPOSES only; nothing executes without the CONDUCTOR's governed path + approval;
  this is not advice, it's governed proposals with reasons.
- **Data-gating:** real candidates need data; the assembly + ranking + persistence are testable with seeded
  evidence.
- **Gate / DoD:** given seeded desk evidence, the board ranks candidates each with a full reason chain and a
  recommended action; no-edge candidates map to DCA; nothing executes without approval; tested.
- **Tests:** ranking determinism; reason-chain completeness; no-edge→DCA; approval still required to act.

### S17.7 — The Kitchen (cockpit: watch + control)  ·  Level 6  ·  size **L**  ·  deps: S17.1, S17.6 (+ S17.2 for desk health)
**Goal:** a live dashboard tab where the founder *watches the desks work* and *steers the board* — without the
web app ever touching the brain directly.
- **Deliverables:**
  - **Brain → bridge:** extend `ops/publish_state` to publish `desk_status` (per-desk: state idle/running/ok/
    retrying/quarantined, last output summary, last-run time, success-rate/freshness metrics) + the `proposals`
    board to Supabase (new tables mirrored from the brain DBs).
  - **Web (Vercel/Next.js):** a new **Kitchen** tab — live desk cards + an Opportunity Board rendered as
    To-Do / Doing / Review.
  - **Control (founder-only):** extend `ops/command_poller` + the Supabase `commands` channel with: **reorder/
    prioritize** a proposal, **approve / veto** a proposal, **pause / resume** a desk, **run-a-desk-now**. The
    **brain executes; the web only requests** — exactly the existing model. Founder-only + fail-closed +
    double allowlist (DB RLS + app), reusing the S-web security pattern.
- **Guardrails:** every control is a *request* the brain validates and the Constitution still gates; a paused
  desk simply doesn't run; approve/veto flows through the existing founder-only gate; no new direct-write path
  from the web to the books.
- **Data-gating:** the cockpit works with whatever state exists (thin until data flows).
- **Gate / DoD:** the Kitchen reflects live desk + proposal state; a founder command (approve / pause / reorder)
  round-trips through the channel and is honored by the brain; a non-founder or off-allowlist request is
  refused; tested (the `tests/test_web_bridge` pattern, extended).
- **Tests:** publish shape; command round-trip per control; founder-only/fail-closed; pause stops a desk run.

### S17.8 — Real LLM desks (the "smarter" layer)  ·  size **L**  ·  FOUNDER/PAID  ·  deps: S17.1–S17.3
**Goal:** replace the deterministic `analyze` bodies of selected desks with real Claude-Agent-SDK desks (the
S12.5 design) where judgment adds value — HERALD (news synthesis), QUANT (thesis review), maybe a research SCOUT.
- **Deliverables:** Agent-SDK desk implementations behind the existing master switch + the S17.2 cost cap; the
  same `EvidenceObject` contract out; narrow/safe learning only (refine retrieval/priors, never the Constitution).
- **Guardrails / cost:** token spend is real → gated by the cost cap + master switch (default OFF) + founder
  enable; evidence-only (no act); everything still flows into Edge Proof.
- **Note:** this is the only sub-sprint that costs money to *run* and is genuinely "AI workforce." Do it LAST,
  once data + the deterministic desks prove the pipeline is worth the tokens.

---

## 3. Dependency graph & recommended order

```
S17.1 Desk framework ──┬──► S17.2 Supervisor ──► S17.3 Scheduler/DAG ──┐
                       ├──► S17.4 Loop self-check                      ├──► S17.7 Kitchen (watch+control)
                       └──► S17.6 Opportunity Board ───────────────────┘
S17.5 Memory (independent, any time)
S17.8 LLM desks (last; founder/paid)
```

**Recommended first slice (max insight, min spend, no new risk):**
**S17.1 → S17.6 → S17.7.** That gets you, end-to-end: named desks → a ranked governed Opportunity Board → a live
Kitchen you watch and steer. Add **S17.2** early if you want the self-healing/cost-cap robustness before the
cockpit. **S17.5** can slot in anywhere. **S17.8** waits until there's data + a proven pipeline.

**If choosing by theme (the founder's words):**
- *"Enhance Level 2 / Body+Loop"* → **S17.4**
- *"Enhance Level 3 / Memory"* → **S17.5**
- *"Enhance Level 5 / Guardrails"* → the **cost cap in S17.2** (+ the proposal self-check S17.4)
- *"Enhance Level 5 / Scheduler"* → **S17.3**
- *"Level 4 / named desks"* → **S17.1** (the foundation for everything)
- *"Level 5 / Supervisor"* → **S17.2**
- *"Level 6 / the Kitchen, watch + control"* → **S17.7** (needs S17.1 + S17.6 first)

---

## 4. What's data-gated vs. buildable-and-testable now

| Sub-sprint | Builds + tests fully WITHOUT data? | Produces REAL output only WITH data |
|---|---|---|
| S17.1 Desks | ✅ (seeded DBs) | richer desk outputs |
| S17.2 Supervisor | ✅ (stub desks) | — |
| S17.3 Scheduler/DAG | ✅ | meaningful cross-desk evidence |
| S17.4 Loop self-check | ✅ | — |
| S17.5 Memory | ✅ | richer patterns |
| S17.6 Opportunity Board | ✅ (seeded evidence) | **real candidates / "where to put money"** |
| S17.7 Kitchen | ✅ (thin state) | a live board with real opportunities |
| S17.8 LLM desks | partial | the judgment layer |

So everything is buildable now; the parts that turn into **real money insight** (S17.6/S17.7 content) light up
the moment the founder adds the free Alpaca + FRED keys.

---

## 5. Guardrail ledger (nothing here weakens the trust-inversion)

- Evidence desks **cannot act** (enforced by class shape + a test) — unchanged from S12.5.
- SCOUT writes data tables only; STEWARD exits and CONDUCTOR buys still pass Edge Proof → Constitution → Budget
  → Approval → Broker. **No desk gets a gate bypass.**
- The supervisor's **cost cap is a new, only-tightens, founder-owned guardrail** (the "runaway bill" rail).
- The proposal self-check **strengthens** the stale/single-source rule at the decision boundary.
- The Kitchen's controls are **requests** the brain validates; the web never writes the books; founder-only +
  fail-closed, reusing the live web-bridge security model. Going live stays the founder's explicit act.
- Phase 0 / paper-only throughout. No sub-sprint moves real money.

---

## 6. Honest expectations

- This makes The Camel **organized, watchable, self-healing, and explainable** — a real step up in usefulness
  and trust. It is the difference between "a governed loop" and "an operator you can watch and steer."
- It does **not** manufacture alpha. With data + Edge Proof it will surface *some* governed opportunities and,
  often, tell you honestly there's no edge and DCA is the right call. At ~$126 + $100/mo, the compounding +
  not-blowing-up the rails already guarantee is what grows the money; the workforce makes that disciplined,
  visible, and ready to scale with capital.
- The **Entrepreneur arm (SCRIBE)** — the cash-flow engine of the original two-arm vision — is a deliberate
  future desk; at this capital level it may move net worth more than any trading signal. Worth a conscious
  decision later.

---

*Pick the slice(s) to execute first; each ships in QA'd batches with an adversarial review before commit, the
same way S16 did.*

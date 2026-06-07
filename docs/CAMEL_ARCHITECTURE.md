# CAMEL ARCHITECTURE — the module map (S14)

> **Canonical home for "where does everything live and how does it fit."** Pairs with the `CLAUDE.md`
> repo map (file-level detail) and `CAMEL_DATA_CONTRACTS.md` (the 7-DB schemas). This doc is the
> **layered view**: how the packages compose into one trust-inverted system.

## The one idea: inversion of trust

The LLM is the *least*-privileged component. It only **proposes**. Every consequential action flows
**down** through deterministic gates it cannot edit, and only acts at the bottom if every gate allows:

```
Observe (regime, S9) ─► Opportunity Router (operator_os) ─► Strategies PROPOSE (strategies)
        │
        ▼
   Edge Proof  (engine/edge_proof.py — 17 checks, S10)        ← evidence gate
        ▼
   Constitution (guardrail/constitution.py)                   ← Sharia #1, risk, phase rails
        ▼
   Budget Kernel (capital/budget_kernel.py)                   ← spend limits / buckets
        ▼
   Human-Approval gate (governance/approval.py)               ← phase-gated, withholds by default
        ▼
   Act — paper (broker/paper) · realistic (execution/) · manual (broker/manual) · live (broker/live, gated OFF)
        ▼
   Measure → Learn (learning/, propose-only L3) → audit (ledger/ hash-chain, op_log)
```

The keystone that strings this together at runtime is **`loop/driver.py`** (`run_strategy_tick`) →
**`loop/assembled.py`** (`AssembledLoop`). A buy with no passing EdgeReport is rejected **by the assembled
loop**, not just in a unit.

## Layers (every package, grouped by what it does)

| Layer | Packages | Role |
|---|---|---|
| **Foundation** | `db/` · `config/` | 7 SQLite DBs + `CamelDbs`; founder-owned `limits.yaml` |
| **Data supply** | `data/` (+`data/connectors/`) · `security/` · `sharia/` | ingest (10 connectors), point-in-time provenance, sanitiser/scraping-policy, whitelist + AAOIFI screen (`sharia/aaoifi.py`, `cross_check.py`) |
| **Knowledge** | `data/entity_resolver` · `trader/regime/` · `trader/events/` | entity graph, 10-state regime engine + SAR/USD peg, event intelligence + `event_reactions` |
| **Evidence** | `engine/` (`edge_proof_v0`, `edge_proof`) · `research/` (dormant) | the 17-check Edge Proof; the analyst-desk framework (evidence-only, master switch OFF) |
| **Decision** | `guardrail/` · `governance/` · `capital/` · `operator_os/` | the Constitution, config-guard/tool-permissions/approval, Allocator + Budget Kernel, state machine + router |
| **Strategy & portfolio** | `strategies/` · `portfolios/` · `learning/` | the trio + dividend_growth + mixer + promotion ladder; 6 portfolios + risk budgets; 4-tier learning |
| **Execution** | `broker/` (`paper`, `manual`, `live`) · `execution/` · `edgelab/` · `sandbox/` | fills (paper/realistic/Sahm-manual/gated-live), the realistic-paper engine + corporate actions, the two-engine backtester + No-Edge protocol, Sandbox Mode |
| **Loop & ops** | `loop/` (`runner`, `assembled`, `driver`, `jobs`, `scheduler`) · `ledger/` · `ops/` | the assembled tick + scheduled jobs, the hash-chain ledger + reconcile, kill-switch/health/backup/live-readiness |
| **Surfaces** | `dashboard/` · `alerts/` | read-only operator dashboard (Design-System skin), Telegram/WhatsApp + founder brief + RED-ALERT |
| **Other arm** | `entrepreneur/` | the Entrepreneur Camel (product gate, separate Constitution, build pipeline) |

## The 7 databases
`camel_market` · `camel_macro` (+ regime_history, event_reactions) · `camel_fundamentals` (company_facts,
assets) · `camel_news` (news_events, event_reactions) · `camel_sharia` (whitelist, sharia_status, etf_holdings)
· `camel_portfolio` (orders, positions, ledger, runs, approvals, portfolios, portfolio_holdings, op_log) ·
`camel_learning` (learning_ledger, edge_reports, learning_proposals, research_evidence). Point-in-time on every
decision-relevant table: `event_date · reported_at · ingested_at · known_at`.

## Physical layout — decision (S14)

The packages above are **flat at the repo root** but already **domain-organized**. The original S14 plan was
to nest them deeper (e.g. fold `engine`/`edgelab`/`execution`/`strategies`/`portfolios` under `trader/`, the
fill models under `broker/`). **That physical reshuffle is deliberately deferred.** Rationale:

- It is **pure churn** — it changes hundreds of `import` statements across ~55 source + ~35 test files for
  **zero functional change**; the only gate is "tests stay green."
- The current layout is already clean and discoverable (this doc is the map); the nesting is cosmetic.
- Doing a big-bang move risks a green 557-test suite for no benefit.

**It is therefore an explicit, optional, separately-scoped task** — best done (if ever) ahead of a packaging
or open-source milestone, as its own focused PR with a full green run, not bundled at a feature finish line.
Tracked in `CAMEL_ROADMAP.md` → Workstreams & Backlog. *Code beats docs; don't break what works.*

# Noah — Documentation Index

**Noah** is a guardrailed autonomous AI operator that runs a continuous
Observe→Thesis→Choose→Act→Measure→Learn loop across two arms — **Trader Noah**
(Sharia-compliant markets) and **Entrepreneur Noah** (Sharia-compliant AI products).
Founder: Chiko (Riyadh). Runtime: Windows 11 PC.

> **North Star:** Noah is a Sharia-compliant autonomous operator with a deterministic
> constitution, an edge-proof engine, a budget kernel, and a learning ledger.
> **LLM proposes. Math tests. Guardrails decide. Human approves high-risk actions.**
> **Safety first. Evidence second. Autonomy last.**

**Status:** Phase 0 (paper) · Sprints 1–3 complete · 110 tests green · 7-DB architecture live.

---

## The documentation set

Each document is the **canonical home** for its topic. Facts live in exactly one place;
the others point here rather than copy. This is the rule that keeps the docs from drifting.

| Document | Purpose | Audience | Canonical for |
|---|---|---|---|
| **`README.md`** (this file) | Orientation + index | Everyone | The map of all docs |
| **`../Noah_CLAUDE.md`** | Agent operating manual: conventions, rails, repo map, status | Claude Code / builder | How to work in the repo |
| **`../HANDOFF.md`** | Current status + tech stack + how to run | New contributor | Onboarding / run instructions |
| **`NOAH_CONSTITUTION.md`** | The rules in prose: Sharia, risk, phase gates | Founder, Sharia scholar, lawyer | The non-negotiable rules |
| **`NOAH_ROADMAP.md`** | Full sprint plan S1–S12 + open decisions | Builder, founder | The build roadmap |
| **`NOAH_DATA_CONTRACTS.md`** | 7-DB schemas, point-in-time discipline, data quality | Builder | Data model + contracts |
| **`NOAH_TESTING.md`** | Test strategy, adversarial suite, integration tests | Builder | How Noah is tested |
| **`NOAH_LIVE_READINESS.md`** | Phase 1 go-live checklist | Founder | The pre-live gate |
| **`NOAH_CHANGELOG.md`** | Sprint-by-sprint history | Everyone | What happened when |

**Authoritative code beats docs.** Where a doc describes a rule, the implementation
(`guardrail/constitution.py`, `config/limits.yaml`) is the final authority. Docs explain;
code enforces.

---

## Reading order

- **New here?** → `../HANDOFF.md`, then this index, then `NOAH_ROADMAP.md`.
- **Building a sprint?** → `../Noah_CLAUDE.md` (conventions + rails) + the sprint in `NOAH_ROADMAP.md`.
- **Reviewing safety/compliance?** → `NOAH_CONSTITUTION.md`.
- **About to go live?** → `NOAH_LIVE_READINESS.md`.

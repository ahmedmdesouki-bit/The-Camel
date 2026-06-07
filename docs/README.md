# Camel — Documentation Index

**The Camel** is a Python-based, guardrailed autonomous operator running a continuous
Observe→Thesis→Choose→Act→Measure→Learn loop across two arms — **Trader Camel**
(Sharia-compliant markets) and **Entrepreneur Camel** (Sharia-compliant AI products). Its
defining principle is an **inversion of trust**: the LLM only *proposes*; a deterministic
**Constitution** it cannot edit, an **Edge Proof** gate, a **Budget Kernel**, audit logs, a
**kill switch**, and **human approval gates** *decide*. Founder: Chiko (Riyadh). Runtime: Windows 11 PC.

> **North Star:** The Camel is a Sharia-compliant autonomous operator with a deterministic
> constitution, an edge-proof engine, a budget kernel, and a learning ledger. Not a stock-picking chatbot.
> **LLM proposes. Math tests. Guardrails decide. Humans approve what's risky. Autonomy is earned, not granted.**
> **Safety first. Evidence second. Autonomy last.**

**Status:** Phase 0 (paper) · Sprints **S1–S7 complete** · **S8 core** (10 connectors) · **S9–S11 complete (+ S11.5 integration)** · **557 tests green** ·
7-DB architecture live · on **Roadmap v3** (S1–S14).

---

## The documentation set

Each document is the **canonical home** for its topic. Facts live in exactly one place;
the others point here rather than copy. This is the rule that keeps the docs from drifting.

| Document | Purpose | Audience | Canonical for |
|---|---|---|---|
| **`README.md`** (this file) | Orientation + index | Everyone | The map of all docs |
| **`../CLAUDE.md`** | Agent operating manual: conventions, rails, repo map, status | Claude Code / builder | How to work in the repo |
| **`../HANDOFF.md`** | Current status + tech stack + how to run | New contributor | Onboarding / run instructions |
| **`CAMEL_BRIEF.md`** | Project context: why, who, real capital, open questions | Outside reviewer, founder | The "why & who" |
| **`CAMEL_CONSTITUTION.md`** | The rules in prose: Sharia, risk, phase gates | Founder, Sharia scholar, lawyer | The non-negotiable rules |
| **`CAMEL_ROADMAP.md`** | Full sprint plan S1–S14 (Roadmap v3) + open decisions | Builder, founder | The build roadmap |
| **`CAMEL_ARCHITECTURE.md`** | The layered module map — how every package composes into the trust-inverted system | Builder | Where everything lives + how it fits |
| **`CAMEL_DATA_CONTRACTS.md`** | 7-DB schemas, point-in-time discipline, data quality | Builder | Data model + contracts |
| **`CAMEL_TESTING.md`** | Test strategy, adversarial suite, integration tests | Builder | How Camel is tested |
| **`CAMEL_LIVE_READINESS.md`** | Phase 1 go-live checklist | Founder | The pre-live gate |
| **`CAMEL_BROKER_MATRIX.md`** | Broker comparison + resolved direction | Founder, builder | The broker decision |
| **`CAMEL_DATA_SOURCES.md`** | Verified data-feed catalogue + connector build-list | Founder, builder | Which data feeds, in what order |
| **`CAMEL_MACHINE_HARDENING.md`** | S6 founder machine-setup checklist (Tailscale, BitLocker, secrets, backups) | Founder | The machine hardening checklist |
| **`CAMEL_ALAA_REVIEW.md`** | Review of Alaa's parallel Camel (founder-facing layer) + adopt/decline + sprint mapping | Builder, founder | What we took from Alaa's build |
| **`CAMEL_CONSULTANT_HANDOFF.md`** (root) | Self-contained snapshot for an external reviewer | Outside consultant | One-doc project briefing |
| **`CAMEL_CHANGELOG.md`** | Sprint-by-sprint history | Everyone | What happened when |

**Authoritative code beats docs.** Where a doc describes a rule, the implementation
(`guardrail/constitution.py`, `config/limits.yaml`) is the final authority. Docs explain;
code enforces.

---

## Reading order

- **New here?** → `CAMEL_BRIEF.md` (why/who), then `../HANDOFF.md` (status/run), then `CAMEL_ROADMAP.md`.
- **Building a sprint?** → `../CLAUDE.md` (conventions + rails) + the sprint in `CAMEL_ROADMAP.md`.
- **Reviewing safety/compliance?** → `CAMEL_CONSTITUTION.md`.
- **About to go live?** → `CAMEL_LIVE_READINESS.md`.

## Archive

`source-materials/` holds the original PRDs, specs, and the StockSense playbook/dashboard —
provenance only, superseded by the docs above.

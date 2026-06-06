# THE CAMEL — BRIEF — project context, founder constraints, open questions

> **Canonical home for the "why & who":** origin story, founder constraints, the real
> capital situation, key decisions and their rationale, and the honest open questions.
> For *current build status* see `../HANDOFF.md`; for the *plan* see `CAMEL_ROADMAP.md`;
> for the *rules* see `CAMEL_CONSTITUTION.md`. This doc is the standalone brief you can
> hand to an outside reviewer.

> ⚠️ Personal, educational decision-support / engineering project for the founder's **own**
> capital. Not financial, legal, or Sharia advice; not a product offered to others.

---

## 1. TL;DR

**The Camel** is a Python-based, always-on, guardrailed autonomous operator running a continuous
loop (Observe → Form Thesis → Choose Path → Act → Measure → Learn) across two arms:
- **Trader Camel** — trades Sharia-compliant markets.
- **Entrepreneur Camel** — builds/launches/sells Sharia-compliant AI products.

Defining principle: an **inversion of trust** — the LLM only *proposes*; every consequential
action (anything touching Sharia compliance, real money, or the live internet) is *decided* by
deterministic machinery the model cannot edit: a **Constitution**, an **Edge Proof** evidence gate,
a **Budget Kernel**, append-only **audit logs**, a **kill switch**, and **human approval gates**
before any live-money autonomy. Aggressive inside the rails, powerless outside them — autonomy is
earned through a paper-trading track record, never granted.

---

## 2. The founder & hard constraints

- **Founder:** "Chiko," Riyadh, Saudi Arabia. Beginner-to-intermediate investor.
- **Day job:** works full-time at a **travel-tech startup** — real domain knowledge that makes
  the Entrepreneur arm's lead product (an Arabic complaint/SLA-response assistant for Saudi
  travel/hospitality operators) a genuine fit, not a guess.
- **Compliance:** **Sharia-compliant only — a hard wall.** Excludes conventional finance,
  alcohol, tobacco, gambling, pork, adult content, **and weapons/defense.** No riba,
  leverage, shorting, options, or derivatives.
- **Risk profile:** moderate; holds through dips, does not panic-sell.
- **Real brokerage today:** the **Sahm** app — **whole shares only**, no fractional, US ETFs/equities.
- **Real capital today:** ~**$126** deployed + **$100/month** contributions (small on purpose —
  a learning-stage account). A separate **$10K "Camel Fund"** is the target working capital for
  the autonomous operator.
- **Base currency:** SAR, pegged ~3.75/USD (USD holdings carry ~no FX risk for the founder).

---

## 3. Origin: two systems merged

1. **StockSense v11** — the founder's own Sharia-compliant investment *discipline*: a Sharia
   gate, a base-rate engine (never "this will go up"; instead sample size, hit rate, what's
   priced in, counter-signals), a written-invalidation-point rule, a research log, and
   three-market scaffolding (US live; Saudi/Egypt later).
2. **A 6-layer "autonomous operator" stack** — a 6-layer blueprint for an autonomous operator living on a real
   machine. Renamed **Camel** and made ours.

**Camel = StockSense v11 (the investing conscience / Sharia auditor) running inside an
operator-stack-style autonomous harness, wrapped by a guardrail layer the original blueprint lacked.**

*(The original source materials — the original PRDs & specs, the StockSense playbook, dashboard,
and tracker — are archived under `docs/source-materials/`.)*

---

## 4. Tooling division

- **Cowork (Claude desktop)** — strategy, research, Sharia scans, dashboards (thinking).
- **Claude Code** — building & running the repo (doing).

---

## 5. Key decisions already made (and why)

- **Guardrails as code, not prompts** — autonomy is only safe if prohibitions are deterministic.
- **Lead with the Entrepreneur arm, leash the Trader arm** — software has bounded downside;
  autonomous trading has ruin risk. Keep live trading human-gated longer.
- **Paper-first** — Alpaca paper proves the guardrails before any real dollar moves.
- **Personal-use only** — managing others' money would trigger Saudi CMA robo-advisory licensing.
- **Pivot the real portfolio SCHD/SCHX → SPUS** — the founder's deployed holdings SCHD + SCHX
  both **fail** the Sharia screen; compliant whole-share swaps identified (SPUS recommended,
  HLAL, MNZL). *(Real-world action item, founder's timing.)*

---

## 6. Open questions for an evaluator 🔎

1. **Edge in trading:** a $10K positional, long-only, Sharia-screened book — is there a
   credible edge, or is the honest expectation "market beta minus costs"? Where could a real,
   defensible asymmetric edge come from under these constraints?
2. **Entrepreneur arm realism:** what's a realistic first compliant AI product an autonomous
   agent could actually ship and monetize, and what's the true success rate?
3. **Guardrail completeness:** what prohibited or ruinous actions do the rules still miss?
4. **Autonomy danger:** where does "auto within guardrails" still bite — data poisoning,
   broker API edge cases, prompt-injection from web data, hallucinated thesis cards?
5. **Broker choice:** Alpaca vs IBKR for live, given KSA residency + self-imposed Sharia whitelist.
6. **Is this worth it?** Brutally: given $126 real capital + $100/mo, is the effort better spent
   on contributions/skill-building than on building an autonomous operator? Argue both sides.

> These questions remain genuinely open and are the right things to pressure-test. The
> roadmap's emphasis on the data backbone (S8), Edge Proof (S4.5/S10) and the Edge Lab
> backtesting (S12) is the project's attempt to answer #1 honestly before risking capital —
> and the Entrepreneur arm (now pulled earlier to S7) is the answer to #2 and #6.
>
> **The "No-Edge Found" protocol (pre-committed):** if the Edge Lab finds no defensible,
> cost-and-Sharia-drag-survived edge, that is **the system working, not failing** — the
> pre-registered fallback is scheduled DCA into SPUS/HLAL, and Phase 1 active trading does not
> proceed. This answer is written down *before* the lab runs so a disappointing result can't be
> rationalised away. (Broker for Phase 1 is resolved: Alpaca for the autonomous US path +
> manual-entry mode for the real Sahm account; IBKR deferred to Phase 2.)

---

## 7. One-line summary

**The Camel is StockSense v11's Sharia-compliant investing discipline, running inside an autonomous
operator where the LLM only proposes and a deterministic constitution decides, earning the right to
real capital through paper-mode evidence — Cowork-for-thinking, Claude-Code-for-doing, on a Windows PC.**

# The Camel

A Python-based, guardrailed autonomous operator running an Observe → Thesis → Choose → Act →
Measure → Learn loop across two Sharia-compliant arms — **Trader Camel** (markets) and
**Entrepreneur Camel** (AI products). Its defining principle is an **inversion of trust**: the
LLM only *proposes*; a deterministic **Constitution** it cannot edit, an **Edge Proof** evidence
gate, a **Budget Kernel**, append-only **audit logs**, a **kill switch**, and **human approval
gates** *decide* what actually happens. Aggressive inside the rails, powerless outside them —
autonomy is earned through a paper track record, never granted.

> **Safety first. Evidence second. Autonomy last.**
> LLM proposes · Math tests · Guardrails decide · Humans approve what's risky · Autonomy is earned, not granted.

**Status:** Phase 0 (paper) · Sprints **S1–S6 complete** · **289 tests green** · 7-DB architecture live ·
on **Roadmap v3** (S1–S14), next **S6.5**.

---

## Where to start

| You want to… | Read |
|---|---|
| Understand the project (why, who, context) | [`docs/CAMEL_BRIEF.md`](docs/CAMEL_BRIEF.md) |
| Get current status + run it | [`HANDOFF.md`](HANDOFF.md) |
| Work in the repo (build a sprint) | [`CLAUDE.md`](CLAUDE.md) — the operating manual |
| See the full plan | [`docs/CAMEL_ROADMAP.md`](docs/CAMEL_ROADMAP.md) |
| Everything else | [`docs/README.md`](docs/README.md) — the documentation index |

## Source of truth

- **Docs:** `CLAUDE.md` (operating manual) + `docs/` (one canonical doc per topic).
  A fact has exactly one home — change a sprint in `docs/CAMEL_ROADMAP.md`, not elsewhere.
- **Code beats docs:** `guardrail/constitution.py` + `config/limits.yaml` are authoritative.
- **History/origin:** the original PRDs, specs, and the StockSense playbook are archived in
  [`docs/source-materials/`](docs/source-materials/).

## Run the tests

The repo path is 261 chars (over Windows MAX_PATH). Map a virtual drive first:

```powershell
subst N: "<path-to-this-folder>"
cd N:\
python -m pytest -q          # 289 passed
```

*(For future work, cloning to a short path like `C:\camel` removes this friction.)*

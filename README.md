# Noah

A guardrailed autonomous AI operator for Sharia-compliant trading and AI-product building.
Every consequential action passes through a deterministic Constitution the agent cannot modify.

> **Safety first. Evidence second. Autonomy last.**
> LLM proposes · Math tests · Guardrails decide · Human approves high-risk actions.

**Status:** Phase 0 (paper) · Sprints 1–3 complete · 110 tests green · 7-DB architecture live.

---

## Where to start

| You want to… | Read |
|---|---|
| Understand the project (why, who, context) | [`docs/NOAH_BRIEF.md`](docs/NOAH_BRIEF.md) |
| Get current status + run it | [`HANDOFF.md`](HANDOFF.md) |
| Work in the repo (build a sprint) | [`Noah_CLAUDE.md`](Noah_CLAUDE.md) — the operating manual |
| See the full plan | [`docs/NOAH_ROADMAP.md`](docs/NOAH_ROADMAP.md) |
| Everything else | [`docs/README.md`](docs/README.md) — the documentation index |

## Source of truth

- **Docs:** `Noah_CLAUDE.md` (operating manual) + `docs/` (one canonical doc per topic).
  A fact has exactly one home — change a sprint in `docs/NOAH_ROADMAP.md`, not elsewhere.
- **Code beats docs:** `guardrail/constitution.py` + `config/limits.yaml` are authoritative.
- **History/origin:** the original PRDs, specs, and the StockSense playbook are archived in
  [`docs/source-materials/`](docs/source-materials/).

## Run the tests

The repo path is 261 chars (over Windows MAX_PATH). Map a virtual drive first:

```powershell
subst N: "<path-to-this-folder>"
cd N:\
python -m pytest -q          # 110 passed
```

*(For future work, cloning to a short path like `C:\noah` removes this friction.)*

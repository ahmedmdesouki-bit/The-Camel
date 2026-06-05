# 🧭 Noah — Stack Review & Windows Runbook
*Companion to Noah PRD v1 · Runtime: your Windows PC · June 2026*

---

## Part A — Stack review: the best tool for each step

The rule: **use the heaviest tool only where it earns its weight.** For Phase 0 on one
Windows machine, several "cloud" choices simplify down to local ones until you actually
need remote/multi-device. Changes from the original ADAM stack are flagged.

| Step / layer | Best tool | Note / change |
|---|---|---|
| Strategy, research, Sharia scans, design, dashboards, decisions | **Cowork** (Claude desktop — here) | The thinking layer; cross-app. Stay here for these. |
| Build & run the repo, tests, the loop | **Claude Code** (in the repo, on your PC) | Edits + runs on the real machine. This is the move from here on. |
| Dev environment | **Native Windows** (PowerShell / Windows Terminal) | Claude Code now runs natively on Windows — WSL2 optional, not required. |
| Language / runtime | **Python 3.12** | Matches the Sprint 1 code. |
| Harness / builder | Phase 0: **plain Python loop** · later: **Claude Agent SDK** | Don't over-engineer. The Agent SDK is the real "Codex/Hermes" — adopt when you need tool-use autonomy. |
| Reasoning models | **Claude API** and/or **OpenAI API** | Base-rate cards, business-model classifier. |
| Database | Phase 0: **SQLite** (local, zero-setup) → **Supabase** later | ⬇️ Simplified. Stand up Supabase only when you need the remote dashboard / multi-device. |
| Broker | **Alpaca paper** → live (or IBKR) | Free paper API; reachable from KSA. |
| Market data | **Alpaca** / yfinance now · **EODHD** for 3-market later | Cost/coverage. |
| Notifications / approvals | **Telegram bot** | ⬇️ Simpler & free vs Pushover; great on Windows. |
| Remote access + kill switch | **Tailscale** (Windows app) | Works natively. |
| Scheduler | **Windows Task Scheduler** | 🔁 Replaces macOS launchd. |
| Secrets | **`.env`** now → **Windows Credential Manager** later | Keep simple for Phase 0. |
| Deploy (Entrepreneur side) | **Netlify** / **Cloudflare Pages** | Static + serverless functions. |
| Version control | **GitHub** + Claude Code | — |
| Disk security | **BitLocker** | 🔁 Replaces FileVault. |

**Bottom line:** Cowork for thinking, Claude Code for building/running, and a deliberately
lean Phase 0 (SQLite + plain loop + Alpaca paper + Telegram) so you're running in days, not weeks.

---

## Part B — Step-by-step: get Noah running on Windows

> Goal of these steps: a green test suite and Claude Code ready to build Sprint 2.
> Nothing here touches real money.

### Step 1 — Install prerequisites
1. **Python 3.12** — install from python.org; tick "Add to PATH". Verify: `py -3.12 --version`.
2. **Git** — install Git for Windows. Verify: `git --version`.
3. **Windows Terminal** (from Microsoft Store) — nicer than the old console.

### Step 2 — Install Claude Code (native Windows)
In **PowerShell**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
irm https://claude.ai/install.ps1 | iex
```
Then run `claude` once to authenticate (follow the login prompt).
*(Alternative, if you prefer npm + Node 18+: `npm install -g @anthropic-ai/claude-code`.)*

### Step 3 — Drop in the Noah repo
1. Unzip `Noah_Sprint1_*.zip` somewhere like `C:\Noah\` → you get a `noah\` folder.
2. It already contains `CLAUDE.md` (Claude Code reads this automatically for context).

### Step 4 — Verify the safety core (the Sprint 1 gate)
In PowerShell, inside the `noah` folder:
```powershell
cd C:\Noah\noah
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```
✅ You should see **`28 passed`**. That's proof every prohibited action is rejected.
(If PowerShell blocks the venv activate script, run the `Set-ExecutionPolicy` line from Step 2.)

### Step 5 — Open the project in Claude Code
```powershell
cd C:\Noah\noah
claude
```
Claude Code reads `CLAUDE.md` and self-briefs. Good first prompts:
- "Read CLAUDE.md and summarize the current state and the Sprint 2 plan."
- "Initialize git, make the first commit."
- "Build Sprint 2 per CLAUDE.md — start with the whitelist + Sharia re-screen module and its tests."

### Step 6 — Get your paper keys (no real money)
1. Create an **Alpaca** account → generate **paper-trading** API keys.
2. Set the key scope **trade-only, withdrawals disabled**.
3. `copy .env.example .env` and paste the paper keys into `.env`. Never commit `.env`.

### Step 7 — Let Claude Code build Phase 0
Work sprint by sprint with Claude Code (S2→S5). After each, it runs `pytest`. You stay the
approver. When the full paper loop has run clean for **28 days with zero guardrail breaches**,
you've earned Phase 1 (capped, human-approved live).

### Step 8 — (Phase 1 prep, later) wiring the controls
- **Telegram bot** for approvals/alerts · **Tailscale** for remote access + kill switch ·
  **Windows Task Scheduler** to run the loop after market close · **BitLocker** on the drive.

---

## Part C — What stays in Cowork vs Claude Code

- **Bring back to Cowork (here):** Sharia scans on new names, strategy/base-rate discussions,
  the dashboard + tracker, reviewing Noah's decisions, research, any doc/deck.
- **Do in Claude Code (your PC):** all repo building, tests, the loop, broker/data integration,
  deployment, the scheduler.

You don't lose anything by switching — same underlying engine, right surface for each job.

---

*Noah · Stack & Runbook · Educational/engineering decision support — not financial, legal, or Sharia advice.*

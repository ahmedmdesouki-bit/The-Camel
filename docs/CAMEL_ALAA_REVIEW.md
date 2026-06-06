# Alaa's Camel — file-by-file review & what we're taking

**Reviewed:** 2026-06-06. Source: a parallel "Camel" build by **Alaa (Aladdin)**, a friend of the founder,
shared for cross-pollination. Reviewed every file line-by-line. **No code copied yet** — this is the
assessment + the docs-only fold into our roadmap.

## What Alaa built (the one-line truth)
Alaa built the **front-of-house** of the same idea we're building the **back-of-house** of. Same vocabulary
(Constitution, Edge Proof Gate, Live-Money Gate, Sahm, SCHD/SCHX, $100/mo DCA, Sharia-first, S7→S14) — but
his artifact is a **human-coaching + visualization layer**, not an autonomous engine. It has **no real
enforcement** (the Constitution/Edge-Proof are referenced as *labels*, not code that blocks anything). That
is exactly the failure mode our roadmap is built to avoid — *and seeing it confirms our "safety core first"
thesis.* The flip side: **his founder-facing surface is far ahead of ours**, and that's where the gold is.

> They are complementary. Ours = the governed engine. His = the cockpit + the coach. The best "Camel" merges
> our enforcement spine with his UX/coaching skin.

## File inventory
| File | What it is | Verdict |
|---|---|---|
| `camel-dashboard.html` (3,928 lines) | Single-file interactive dashboard: multi-profile, watchlist w/ live prices, milestone tracker, boardroom view, DCA view, analyze view, strategy quiz, mix-analysis | **ADAPT** — richest asset here |
| `camel-coach.skill` / `camel-coach/SKILL.md` | A packaged **Claude Skill** = the conversational coaching front door (commands + portfolio state + 19 frameworks) | **ADAPT** — we have no founder-facing skill |
| `camel-coach/references/analysis-frameworks.md` | Detailed methodology for 19 analytical frameworks | **HARVEST** specific frameworks |
| `camel-coach/evals/evals.json` | 3 eval tests for the coaching skill (SHOW DASHBOARD / Analyze / RED ALERT) | **ADOPT pattern** — we have no LLM-output evals |
| `price_server.py` + `price_server.ps1` | Local proxy that serves the dashboard AND fetches Yahoo/stooq server-side to dodge browser CORS | **NOTE** — prototyping trick only |
| `camel_summary.ps1` | Daily portfolio brief → **WhatsApp via CallMeBot**; RED ALERT if drop >3%; Live-Money Gate status | **ADOPT** — brief template + WhatsApp channel |
| `SCHEDULE DAILY SUMMARY.bat` / `START CAMEL DASHBOARD.bat` | Windows Task Scheduler registration + dashboard launcher | **NOTE** — simpler cousin of our `loop/scheduler.py` |
| `README.md` | Cowork-folder orientation | context only |

---

## ADOPT / ADAPT — what improves our Camel (mapped to sprints)

1. **Founder-panic protocol ("RED ALERT").** A 3-step human-factors guardrail: *breathe* (acknowledge the
   emotion) → *assess* (has the thesis actually changed, or is it price noise?) → *act or hold* (confirm hold
   with reasoning, or surface ONE structured option). We have hard guardrails against the *machine*
   misbehaving but **nothing protecting against the human operator's emotions** — a real risk vector in a
   manual-execution (Sahm) loop. → fold into the **Constitution (human-factors section)** + the **S13
   micro-live human approval gate** + the daily-brief generator (auto-fire on daily drop > 3%).

2. **`UPDATE FROM SCREENSHOT` (OCR a Sahm screenshot → prices/positions/cash).** Genuinely clever for a
   broker with **no execution API** — which is exactly our Sahm `ManualBroker` situation. Turns the painful
   manual-entry step into "paste a screenshot." → enhancement to **`broker/positions.py` manual-entry flow**
   + **`CAMEL_BROKER_MATRIX.md`** (note OCR-assisted entry; still writes to the append-only ledger and must
   reconcile — the screenshot is an *input convenience*, not a trust shortcut).

3. **Strategy-fit quiz + strategy-metadata schema.** 5 questions (risk / horizon / research-capacity /
   capital / priority) score each strategy 0–100 and surface a top-3. Each strategy carries structured
   metadata: `horizonScore · riskScore · capitalScore · researchScore · sharia(yes/partial) + note ·
   priority[] · stocks[] · note`. We have a *registry* but no **founder-facing "which strategy fits me"
   selector** and no lightweight fit-metadata. → fold the **metadata fields into the S11 Strategy Registry**
   and add a **strategy-fit selector** as a founder-facing helper (it *proposes*; Edge Proof still decides).

4. **Strategy "mix analysis" / coherence guardrail.** When you add an off-strategy ticker, it warns and
   shows the *impact* of mixing (risk delta, horizon clash, Sharia conflict, diversification benefit). This
   is the UX face of our **strategy-portfolio matrix** (`allowed/forbidden_portfolios`) — but it explains
   *why* a pick is off-strategy instead of silently rejecting. → fold as the **founder-facing rendering of
   the S11 matrix** (surface the reason, not just the verdict).

5. **Interactive dashboard (the real prize).** Multi-profile (localStorage), live-price watchlist, milestone
   tracker, boardroom (operator-terse) view, DCA view, analyze view — all in one dependency-free HTML file.
   Our S6 dashboard is *read-only* and our S10 *decision-quality* dashboard is still a spec. → use Alaa's
   HTML as the **visual/interaction starting point for the S10 decision-quality dashboard + S11 portfolio
   views**, re-wired to read our real DBs (and, critically, to render the *rejections-with-reasons* that are
   the whole point of our system — his dashboard shows holdings, ours must show *why a trade was blocked*).

6. **Daily brief + WhatsApp/CallMeBot channel.** A clean daily-brief template (portfolio · P&L · blitz status
   · cash-drag · **Live-Money Gate X/10** · Constitution status · auto RED ALERT on drop > 3%) delivered over
   **WhatsApp via CallMeBot** (zero-cost). We use Telegram (S6). → add **WhatsApp as a second alert channel**
   and adopt the **brief format** (esp. always showing the Live-Money-Gate counter — good discipline).

7. **Eval harness for LLM-facing surfaces.** `evals.json` asserts behavior ("does NOT recommend panic
   selling", "acknowledges emotion first", "runs Sharia filter"). We have pytest for the *engine* but **zero
   evals for any LLM output**. → adopt the **eval pattern** for the S12.5 Research Desk agents and any
   founder-facing coaching skill (assert the agent never proposes a banned action, always cites sources, etc.).

8. **A founder-facing "camel-coach" Skill itself.** The whole packaged Skill is a real artifact we lack: the
   **human Q&A/coaching interface** to the system, distinct from the autonomous engine. → consider a
   **`camel-coach` skill** in our repo that reads our actual portfolio/edge-proof/regime state (not Alaa's
   hardcoded numbers) — the conversational complement to the dashboard. New small workstream (founder-tools),
   sits *outside* the trust boundary (read-only; proposes, never executes).

### Specific analytical frameworks worth harvesting (into Edge Proof / regime / quality_momentum)
- **Cash-Drag Efficiency Ratio** (idle cash ÷ total; alert > 10%) — simple, we don't track it explicitly.
- **Yield-on-Cost Accumulator** (dividend ÷ original cost; projects forward at dividend CAGR) — natural fit
  for the S11 `dividend_growth` strategy's reporting.
- **Moat Assessment Matrix** (1–5 across switching-costs / network-effects / cost-advantages / intangibles /
  efficient-scale → Wide/Narrow/No) — a structured qualitative input for `quality_momentum` / Edge-Proof
  check #14 (counter-signal inventory) and the fundamentals agent.
- **Sector-Correlation Guardrail** (no sector > 40%, *including ETF look-through*) — we have ETF look-through
  (S8/S9); add the concentration *cap* as a portfolio risk-budget rule (S11).
- **Washington-to-Wall-Street Radar** (policy → sector → ticker mapping) — maps onto our news/geopolitical
  agent (S12.5) + GDELT/ACLED substrate; a good *output template* for that agent.
- **Macro Risk Array** (Fed-rate · CPI · SAR/USD-peg) — the SAR/USD-peg monitor is **net-new** and correct
  for a KSA-resident; add a peg-stability check to the regime/macro layer (S9). Peg intact ⇒ no FX risk, but
  flag peg stress.

---

## DECLINE / DO-NOT-COPY (where ours is correct and his is the looser/older approach)
- **Sharia screen = "debt ÷ total assets < 33%".** This is the older/looser Dow-Jones-style screen. **Keep
  OURS** — the full AAOIFI spec from `CAMEL_DATA_SOURCES.md` (debt ÷ 12-mo-avg-mktcap ≤ 30%; cash + interest-
  bearing ÷ 12-mo-avg-mktcap ≤ 30%; (cash + receivables) ÷ total assets ≤ 67%; non-compliant revenue ≤ 5%;
  11 prohibited sectors). Adopt his *presentation* (a clear PASS/BORDERLINE/FAIL coaching verdict), not his
  thresholds.
- **Hardcoded `ANALYSIS_DATA` (static AAPL/SCHD/SCHX verdicts).** Demo placeholders — the opposite of our
  computed, point-in-time Edge Proof. Don't adopt; our evidence engine replaces it.
- **No enforcement layer.** His Constitution/Edge-Proof are labels, not gates. We keep our deterministic
  enforcement as the spine; his UX rides *on top of* it, never replaces it.
- **localStorage-only persistence.** Fine for a coaching toy; not for our audit-grade hash-chain ledger.
- **Yahoo/stooq as price source.** Already classified prototyping-only in `CAMEL_DATA_SOURCES.md`. The
  *local-proxy-to-dodge-CORS* trick is worth remembering if our dashboard ever needs client-side live prices,
  but the data source itself stays Alpaca/our connectors for anything decision-grade.
- **Dividend Capture as a strategy.** He lists it (with tax-drag caveats); we've already settled on
  dividend-*growth*, not *capture*. Consistent — no change.

---

## Net effect
Alaa's build is a **validation + a gift of UX**: it independently lands on our exact problem framing, and it
hands us a mature founder-facing layer (dashboard + coaching skill + daily ritual + screenshot-OCR + panic
protocol) that we'd deprioritized in favor of the safety core. The merge thesis: **our enforcement engine +
his cockpit/coach, with every one of his surfaces re-wired to read our real governed state and to respect
(never bypass) the Constitution + Edge Proof.** Folded into the roadmap at S6 (alerts), S9 (peg monitor),
S10 (dashboard + cash-drag), S11 (strategy-fit + metadata + mix UX + sector cap + yield-on-cost), S12.5
(evals + radar template), S13 (panic protocol + screenshot-OCR manual entry), plus a new **founder-tools**
workstream for the coach skill.

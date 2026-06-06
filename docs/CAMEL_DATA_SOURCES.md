# CAMEL DATA SOURCES — verified catalogue + connector build-list

> **Canonical home for the data-feed decisions.** Output of a deep-research pass (2026-06-06):
> 5 search angles → 25 sources fetched → 96 claims → 25 adversarially verified (3-vote), **25
> confirmed / 0 killed**. This doc drives the S8 connector backlog + S8.5 streaming tier + the S9
> Sharia cross-check ratios. Pricing/terms change — **re-verify at procurement time.**

**How to read:** ✅ **Verified** (3-0 confirmed this pass) · 🔎 **Lead** (source found, not independently
verified) · ⚪ **Unverified** (requested but not confirmed — treat claims as open). 🟢 already built · 🟡 backlog.

---

## Category 1 — Historical market data (prices / corporate actions / dividends / survivorship)

| Source | Tier | Access | Survivorship / PIT | Dividends/CA | Verdict |
|---|---|---|---|---|---|
| **Sharadar** (via Nasdaq Data Link: SEP equity, SFP fund) | Paid | API/bulk | ✅ **~25yr, survivorship-bias-free, point-in-time** (active + delisted) | yes | ✅ **paid PIT anchor for the Edge Lab (S12)** |
| **Alpaca** (IEX) | Free/paid | API + **websocket** | adjusted; not survivorship-curated | splits/divs | 🟢 built (prices) — also the streaming candidate |
| EODHD EOD + Splits/Dividends API | Paid (~$20–60/mo) | API/bulk | adjusted history | ✅ ex-div, yield, payout, splits | ✅ see Cat-2 (powers `dividend_growth`) |
| Norgate · Polygon · Tiingo · CRSP · FMP · Alpha Vantage · Twelve Data | mixed | API/file | ⚪ not verified this pass | — | ⚪ candidates; verify before relying |
| **yfinance / Stooq** | Free | scrape | ⚠️ **survivorship-prone / scrape-only** | unreliable | ⚠️ **prototyping only, never production** |

**Pick:** keep **Alpaca** for live US prices (built); add **Sharadar** as the survivorship-free **point-in-time
anchor when the Edge Lab (S12) needs honest backtests**. Cross-check daily prices Alpaca × (EODHD or Sharadar).

## Category 2 — Fundamentals + Sharia screening ⭐ (highest-value output)

| Source | Tier | Access | Notes | Verdict |
|---|---|---|---|---|
| **SEC EDGAR XBRL** (companyconcept / companyfacts / frames) | **Free** | API, **no key** | US-GAAP/IFRS, comparable across companies+time; **needs a User-Agent (name+email), ~10 req/s** | 🟢 **built** — the free anchor |
| **EODHD fundamentals + Splits/Dividends** | Paid (~$20–60/mo) | API | ~11k US tickers, 10k ETFs; EPS/ROE/EBITDA/margins + **ex-div/yield/payout/splits** | ✅ **paid cross-check + dividend data** |
| **Zoya** | Consumer (Pro) | app/api | **AAOIFI default**, switchable to S&P/MSCI/DJ/FTSE; debt & interest-assets ≤30% of mkt-cap, non-compliant rev ≤5% | ✅ **configurable Sharia ground-truth / cross-check** |
| **IdealRatings / FTSE Russell Islamic methodology** | Index spec | PDF | the screener behind FTSE Islamic indices — gives the **exact AAOIFI ratios** (below) | ✅ **the SPEC for our in-house S9 screen** |
| Musaffa · S&P/MSCI/DJ Islamic index feeds | mixed | — | ⚪ not verified this pass | ⚪ candidates |

**⭐ AAOIFI ratio spec (verified, from the FTSE/IdealRatings methodology) — implement these in the S9 Sharia cross-check:**
- interest-bearing **debt** ÷ trailing-12-mo avg market cap **≤ 30%**
- (cash + deposits + interest-bearing investments) ÷ 12-mo avg market cap **≤ 30%**
- (cash + deposits + receivables) ÷ total assets **≤ 67%**
- non-compliant-activity revenue + non-operating interest income **≤ 5%** of total income
- **11 prohibited sectors:** alcohol, gambling, pork, tobacco, conventional finance, conventional insurance,
  defense, adult entertainment, hotels, music, cinema/broadcasting
- *(Note: Zoya uses plain market cap for the 30% screens; AAOIFI/IdealRatings use the **12-month average** —
  a real, documented difference. Our in-house screen should follow AAOIFI 12-mo-avg and use Zoya as the cross-check.)*

**Pick:** **SEC EDGAR (free) is the fundamentals anchor** (built). Build the **in-house AAOIFI screen to the
IdealRatings spec above**, and use **Zoya as the independent cross-check** — *disagreement → freeze for new buys,
reduce-only exits, human review* (this is exactly the S9 cross-check rule). Add **EODHD** as the paid second
fundamentals source (and the dividends/corporate-actions feed for `dividend_growth`).

## Category 3 — News & events (structured/event-grade; never raw text to the LLM)

| Source | Tier | Structured? | Verdict |
|---|---|---|---|
| **GDELT Cloud** (Events/Stories/Entities; ACLED-style conflict coding) | Free | ✅ structured events | 🟢 built — free event anchor |
| **SEC EDGAR RSS** (10-min cadence; CIK/accession/form + zip XBRL) | Free | ✅ structured filings | 🟡 backlog (8-K/filing events) |
| **Benzinga Newsfeed API** (symbols/ISIN/CUSIP/GICS/tags + "Why Is It Moving") | Paid (affordable) | ✅ structured + WIIM | ✅ phase in as the affordable commercial feed (REST/poll, not websocket) |
| **RavenPack Edge** (sentiment/entities/events/impact) | **Enterprise** (no public pricing) | ✅ analytics | ⚪ **defer** — institutional; not a personal option |
| Marketaux · NewsAPI · Tiingo/Polygon news | mixed | partial | ⚪ not verified |

**Pick:** **GDELT + SEC RSS** free first (structured only); **Benzinga** when commercial news matters; **RavenPack
deferred**. Cross-check an event across GDELT × SEC RSS × Benzinga before it's decision-grade (quorum ≥2).

## Category 4 — Macro / geopolitical / event-reaction

| Source | Tier | Access | Verdict |
|---|---|---|---|
| **FRED + ALFRED (vintage)** | Free | API | 🟢 built — macro anchor (ALFRED vintage = honest point-in-time) |
| **Treasury · World Bank · BLS · BEA · EIA** | Free | API | 🟢 built |
| **Caldara–Iacoviello GPR index** (Fed; 1985–present, GPRH→1900) | Free, **CC BY 4.0** (storable/redistributable w/ attribution) | Excel file | 🟡 backlog — geopolitical-risk + event-reaction anchor |
| **OFAC sanctions list** | Free | API/file (primary confirmed) | 🟡 backlog — compliance exclusions |
| **ACLED** (conflict/protests) | Free (key) | API | 🟢 built |
| EPU index · IMF · OECD | Free | file/API | ⚪ not verified this pass |

**Pick:** macro anchor already built (FRED/ALFRED + 5 more); add **GPR** (file, CC-BY) and **OFAC** from the backlog.

---

## Recommended build order (free-first → paid phased; multi-source cross-check)

1. **Already wired (validated by this research):** SEC EDGAR ✅, FRED/ALFRED + Treasury/World Bank/BLS/BEA/EIA ✅,
   GDELT ✅, ACLED ✅, ETF holdings ✅, Alpaca prices ✅. *The research confirmed these were the right free/official picks.*
2. **Next free connectors (S8 backlog):** SEC RSS (8-K events), GPR (CC-BY file), OFAC sanctions.
3. **In-house AAOIFI Sharia screen to the IdealRatings spec + Zoya cross-check** → the **S9 Sharia cross-check** slice.
4. **First paid add — EODHD** (fundamentals cross-check + dividends/corporate-actions → powers `dividend_growth`, S11).
5. **Backtest-grade paid — Sharadar** (survivorship-free PIT) → when the **Edge Lab (S12)** needs honest history.
6. **Commercial news — Benzinga** when news-driven strategies arrive; **RavenPack** only at an enterprise tier (likely never).

**Cross-check pairings (quorum ≥2):** fundamentals = SEC EDGAR × EODHD · prices = Alpaca × (EODHD|Sharadar) ·
Sharia = in-house AAOIFI × Zoya · news = GDELT × SEC RSS × Benzinga · geopolitical = GPR × EPU × ACLED.

---

## Follow-up research — RESOLVED (2026-06-06, direct web verification)

*(The deep-research workflow failed on a harness/schema error, so these two gaps were verified directly via
web search + primary-source fetches. Findings below are sourced; pricing is volatile — re-verify at procurement.)*

### Gap 1 — Real-time / streaming for S8.5 (monitoring-only) — RESOLVED

| Source | Free websocket? | Real-time or delayed | Limits | Cost for real-time | Verdict |
|---|---|---|---|---|---|
| **Alpaca** | ✅ yes | **Real-time** (IEX exchange only on free) | IEX feed only (single exchange) | free (IEX); SIP/full-market = paid Algo Trader Plus | ✅ **primary S8.5 stream** (already our price source) |
| **Finnhub** | ✅ yes | **Real-time** | **≤ 50 symbols** free; 60 calls/min | free | ✅ **free cross-check stream** (quorum ≥2) |
| Polygon.io (now "Massive") | ❌ | real-time only on **$199/mo Advanced**; free/cheap = 15-min delayed | — | $199/mo | ⚪ too pricey for real-time |
| Twelve Data | mostly paid | websocket paid (Pro+) | free REST = 8 req/min | Pro+ | ⚪ skip for streaming |
| Tiingo | — | EOD-focused, not streaming | — | — | ⚪ not a streaming pick |

**Pick for S8.5:** **Alpaca IEX websocket (primary) + Finnhub free websocket (cross-check, ≤50 symbols).** Both
true real-time, both **free**, both fit a monitoring-only tier on a whitelist of a handful of names — **no new
paid spend.** IEX is a single exchange (partial volume) — fine for monitoring, never treated as decision-grade
tape alone (quorum rule). *Sources: alpaca.markets/data, docs.alpaca.markets streaming; finnhub.io websocket docs; polygon.io pricing.*

### Gap 2 — Saudi (Tadawul) / Egypt (EGX) data + the Sahm-API verdict — RESOLVED

| Source | Market | What it provides | Access / pricing | Verdict |
|---|---|---|---|---|
| **Sahm / SAHMK Developers API** | **Saudi (Tadawul)** | **DATA ONLY** — REST quotes, **realtime websocket (Pro+)**, historical OHLCV/adjusted, financials | API key; free **100 req/day**, Starter **$149/mo** (5k/day), Pro $499/mo | ✅ **Saudi data connector** — but ⛔ **NO order-placement/execution endpoints** |
| **Twelve Data** | Saudi (XSAU) | EOD (delayed) equities | Pro+ paid plan | 🔎 alt Saudi EOD source |
| **EODHD** | **Egypt (EGX)** | **279 tickers**, EOD + fundamentals (EGP) | free tier; paid from **$19.99/mo** | ✅ **Egypt data connector** |
| Thndr / Telda (Egypt) | Egypt brokers | retail apps | — | ⚪ no retail execution API confirmed |

**⭐ Sahm-API verdict (the key question):** **Sahm HAS a usable *data* API, but NOT a *trading/execution* API.**
The SAHMK Developers API is **market-data only** (quotes, realtime websocket on Pro+, historical, financials; `X-API-Key` auth) — its docs list **no order/execution endpoints**. So **the broker matrix's "Sahm = manual-entry
for execution" assumption HOLDS** (autonomous order placement via Sahm is still not possible). *But* we gained a
genuine **Saudi (Tadawul) market-data source** — Sahm's data API (free 100 req/day likely covers a small EOD
whitelist; $149/mo if more is needed). *Source: sahmk.sa/en/developers (fetched).*

**Saudi/EGX data path (when those markets come online, post-US):** Saudi = **Sahm Data API** (Tadawul-licensed,
local; free tier first) or Twelve Data; Egypt = **EODHD EGX** ($19.99+). **Execution for both stays MANUAL**
(Sahm for Saudi/US-ETF; Thndr/Telda for Egypt) — no retail execution API confirmed for autonomous order placement.

## Caveats (honest)
- **Only a subset was verified in depth.** Confirmed: Sharadar, SEC EDGAR, EODHD, Zoya, IdealRatings/FTSE, GDELT,
  SEC RSS, Benzinga, RavenPack, GPR. **Not independently verified:** Polygon, Tiingo, Alpaca-data-specifics, Norgate,
  CRSP, FMP, Alpha Vantage, Twelve Data, yfinance, Stooq, Musaffa, index feeds, Marketaux/NewsAPI, FRED/ALFRED
  *specifics*, EPU, OFAC *specifics*, IMF/OECD.
- **Pricing is volatile** (EODHD $19.99 entry vs ~$59.99 standalone fundamentals); re-verify before paying.
- **Licensing/storage/redistribution terms were NOT confirmed** for Sharadar / EODHD / Benzinga — check whether a
  personal user may store/retain derived data before relying on them.
- **Vendor self-description:** Sharadar's survivorship-free claim is corroborated but originates as marketing.
- **SEC EDGAR access:** "no key" ≠ "no rules" — a `User-Agent` (name+email) is mandatory; ~10 req/s; naive fetchers get 403.

## Sources (verified findings)
SEC EDGAR APIs · Sharadar/Nasdaq Data Link (SEP/SFP) · QuantRocket · EODHD (fundamentals + splits/dividends) ·
Zoya (help + blog) · LSEG/FTSE Russell IdealRatings Islamic methodology (PDF) · GDELT Cloud docs · SEC structured
RSS · Benzinga API docs · RavenPack Edge · policyuncertainty.com (GPR) · matteoiacoviello.com · Fed IFDP #1222 ·
OFAC sanctions-list-service · ACLED · (leads) sahmk.sa/developers, twelvedata XSAU, eodhd EGX.

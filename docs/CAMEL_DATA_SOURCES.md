# CAMEL DATA SOURCES — verified catalogue + connector build-list

> **Canonical home for the data-feed decisions.** Output of a deep-research pass (2026-06-06):
> 5 search angles → 25 sources fetched → 96 claims → 25 adversarially verified (3-vote), **25
> confirmed / 0 killed**. This doc drives the S8 connector backlog + S8.5 streaming tier + the S9
> Sharia cross-check ratios. Pricing/terms change — **re-verify at procurement time.**

**How to read:** ✅ **Verified** (3-0 confirmed this pass) · 🔎 **Lead** (source found, not independently
verified) · ⚪ **Unverified** (requested but not confirmed — treat claims as open). 🟢 already built · 🟡 backlog.

---

## ⭐ Operating plan (2026-06-07 expansion) — decision-first + tiered ingestion

> **The discipline (founder directive): "don't exhaust the system."** We *catalogue* widely so we know what
> exists, but we *ingest* a lean **decision-critical core + one quorum cross-check per category** — and phase
> paid sources in only when a real decision needs them. More feeds ≠ better; **evidence density, not feed count.**
> A second pass (2026-06-07) re-verified the catalogue live and roughly **doubled the free options per category**,
> with special weight on the two pillars the founder flagged as key: **historical data** and **news data.**

### What each Camel decision actually needs (map data → decision, not data → hoarding)
| Decision the Camel makes | Data it needs | Tier-0 core source (mostly already built) |
|---|---|---|
| **Edge Proof** — is there a real, survivorship-free edge? | PIT prices + benchmark + delisted names | Alpaca/Stooq (built) → **Sharadar** (T2 paid) for honest backtests |
| **Regime** classification (S9) | rates, yield curve, CPI, unemployment, HY spread, **VIX**, USD, oil, **USD/SAR peg** | **FRED/ALFRED** (built) + `VIXCLS` + **`DEXSAUS`** (USD/SAR — activates the peg monitor, free) |
| **Sharia screen** (S9 slice 4) | fundamentals (debt/cash/receivables/revenue) + corp actions | **SEC EDGAR** (built) + EODHD (T2) + **Zoya** cross-check |
| **Event intelligence** (S9 slice 3) | structured news *events* (never raw text) | **GDELT** (built) + **SEC RSS** + Marketaux (entity-tagged) |
| **event_reactions / event studies** (S9.3 → S10) | econ + earnings **calendars + surprise (actual − consensus)** + reaction returns | **FRED/ALFRED** (event dates + PIT) + **Finnhub** (EPS surprise, free) + **CFTC COT** + **Kenneth French** factors |
| **Geopolitical risk** (Gulf-relevant) | chokepoint shipping, geopolitical-risk index, sanctions | **IMF PortWatch** (Hormuz/Red Sea, daily, free) + **GPR** (Saudi series) + **OFAC/UK Sanctions List** |
| **Dividend strategy** (S11) | dividends, ex-dates, corporate actions | **EODHD** Splits/Dividends (T2) |
| **Monitoring** (S8.5, no execution) | streaming quotes + live news | **Alpaca IEX WS + Finnhub WS** (both free) |

### Tiered ingestion plan (what we actually build vs. merely catalogue)
- **T0 — Decision-critical core (FREE; ingest now/next):** SEC EDGAR · FRED/ALFRED (+ `DEXSAUS`, `VIXCLS`, NFCI/STLFSI) · Treasury/World Bank/BLS/BEA/EIA · GDELT · ACLED · ETF-holdings · Alpaca prices — **all built** — plus the cheap free adds: **SEC RSS (8-K events), Finnhub (EPS surprise + free WS), CFTC COT, Kenneth French factors, CBOE/FRED stress series, IMF PortWatch, GPR/EPU, OFAC + UK Sanctions List**, and **SAHMK** (free Saudi).
- **T1 — Quorum cross-check (free/cheap; the redundancy layer):** the *second* independent source per category (see "Quorum pairs" below). One free + one independent is the rule; we don't need a third unless they disagree.
- **T2 — Paid phase-in (only when a decision needs it):** **Sharadar** (PIT/survivorship-free US fundamentals — top paid priority, gates honest Edge Lab) · **EODHD All-World** (fundamentals + dividends + the one API spanning US+Tadawul+EGX) · **Benzinga or Tiingo News** (commercial/archive news) · **Trading Economics API** (clean cross-country consensus/surprise).
- **T3 — Reference / seed / manual ONLY (never a live decision input):** Kaggle dumps, official-exchange web pages, Argaam (Saudi earnings, scrape), OPEC MOMR (PDF), ICG CrisisWatch (narrative) — all behind the sanitization firewall, used for backfill/context, never auto-acted on.

### Quorum pairs (≥2 independent sources before anything is decision-grade)
- **US prices:** Alpaca/Polygon × Stooq · **US fundamentals:** SEC EDGAR × EODHD (× FMP third) · **PIT backtest:** Sharadar × SEC EDGAR
- **Sharia:** in-house AAOIFI screen × Zoya · **US news event:** SEC 8-K RSS × Marketaux/GDELT · **US macro:** Fed RSS × ECB RSS
- **Regime/risk:** GPR × EPU · **Geopolitical event:** GDELT (fast) × ACLED/UCDP (verified) · **Chokepoint:** IMF PortWatch × IEA × Brent price · **Sanctions:** OFAC × OpenSanctions
- **Saudi:** SAHMK × EODHD (tie-break saudiexchange.sa) · **Egypt:** EODHD × Twelve Data XCAI (tie-break egx.com.eg)

### 🟢 Two roadmap gaps now have FREE answers (2026-06-07)
- **USD/SAR peg monitor** (`trader/regime/peg.py`, Workstream D / S9 slice 4): **FRED series `DEXSAUS`** is the free USD/SAR spot rate — and we *already have a FRED connector*. **Activates the peg monitor for $0.**
- **event_reactions substrate** (S9 slice 3): build it free from **FRED/ALFRED** (event dates + point-in-time vintages) + **Finnhub** (EPS/revenue surprise) + **CFTC COT** + **Kenneth French** factors, joined to Stooq/Yahoo index returns.

### New free anchors discovered this pass (add to S8 backlog, prioritized)
**SAHMK** (Tadawul-licensed, free 100/day — single best free Saudi source) · **IMF PortWatch** (daily chokepoint shipping — high value for a Gulf investor) · **GPR + EPU** (also on FRED) · **CFTC COT** (positioning API) · **Kenneth French / AQR** (factor libraries) · **CBOE** (VIX/VVIX/put-call) + **FRED NFCI/STLFSI** (stress) · **Marketaux** (entity-tagged news, tags Tadawul+EGX) · **OpenSanctions** (337 sources in one) · **Finnhub** (EPS surprise + free WS).

### ⚠️ Operational flags (don't let these silently rot)
- 🔴 **OFSI Consolidated List CLOSED 28 Jan 2026** → any sanctions ingest must point at the **UK Sanctions List (UKSL)**, not OFSI.
- **UCDP API now needs a free token** (Feb 2026) — request before relying on it.
- **OpenSanctions is free only non-commercially** — fine for personal-use Camel; license needed if it ever monetizes.
- **MENA has NO native clean government/exchange news API.** Saudi (Efsah/Tadawul) and Egypt (EGX/FRA) disclosures are HTML-only → route through licensed third-party APIs (SAHMK, Twelve Data, EODHD) + entity-tagging aggregators (Marketaux), behind the structured-event firewall. **Egypt is the weakest link.** Keep MENA quorum ≥ 2; treat any single MENA fundamental as provisional.
- **Live-pull friction is real** (re-confirmed by direct test 2026-06-07): SEC 403s generic user-agents (send name+email UA), GDELT 429s under load (needs backoff), Yahoo/Stooq are scrape-grade (no SLA). The `SourceConnector` framework — descriptive UA, retry/backoff, recorded fixtures, schema-parsing, sanitization — exists precisely to absorb this. **Hardening backlog: add retry/backoff + UA discipline to the connector base.**

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

**Expanded roster (2026-06-07, verified live) — the historical pillar in depth:**
| Source | Free/Paid (price) | API + key? | History depth | Coverage (US/Tadawul/EGX) | Note |
|---|---|---|---|---|---|
| **SEC EDGAR XBRL** | Free | REST, no key (UA req) | Full filing history | US | Ground-truth US fundamentals (built) |
| **FMP** | Free 250/day; ~$22/mo | REST, key | 30yr fundamentals; **delisted w/ IPO+delist dates** | US ✅, MENA per-ticker verify | Cheap survivorship cross-check |
| **Tiingo** | Free (US daily); ~$30/mo | REST, key | Decades US EOD | US deep | **Dedicated corporate-actions API** (clean splits/divs) |
| **Polygon.io** | Free (5/min, 2yr); ~$29/mo+ | REST + **WS**, key | 15–20yr (paid) | US deep | Gold-standard US tick/intraday; no MENA |
| **Marketstack** | Free 100/mo; ~$10–50/mo | REST, key | ~30yr (paid) | US ✅ Tadawul ✅ EGX ✅ global | Aggregator; intraday history capped |
| **Norgate** | ~$30–80/mo (no true free) | local engine (not REST) | Decades, survivorship-free | US/AU | Best EOD backtest universes; local app |
| **SimFin** | Free tier; ~$30/mo | Python + REST, key | multi-yr | US + intl (MENA thin) | Statements linked to filings |
| **Stooq** | Free | CSV, no key | Decades (varies) | US ✅ global partial; TASI index | Free cross-check, no SLA (built-adjacent) |
| — **MENA** — | | | | | |
| **SAHMK** ⭐ | **Free 100/day** (15-min delay); $149+/mo | REST + **WS**, key | historical (depth verify) | **Tadawul ✅✅** | **Tadawul-licensed — best free Saudi source** |
| **EODHD All-World** ⭐ | Free trial; ~$20–80/mo | REST, key | EOD long; delisted post-2018 | US ✅ Tadawul ✅ **EGX ✅✅** | **The one API spanning all 3 markets** |
| **Twelve Data** | Free 800/day (US); MENA = paid | REST + WS, key | multi-yr | US ✅ Tadawul (Pro+) EGX (paid) | MENA gated behind paid tiers |
| Official exchanges (saudiexchange.sa / egx.com.eg) | Free web; bulk=licensed | web/CSV | long official | each own market | **Quorum tie-breaker** (no clean API) |
| Kaggle dumps · tasi R pkg | Free | download | snapshot (stale) | Tadawul/EGX | **T3 seed only** — not PIT, goes stale |

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

**Expanded roster (2026-06-07, verified live) — the news pillar in depth.** Hard rule reminder: **structured/
sanitized events only — raw article text never reaches the LLM.** Prefer clean APIs/feeds over scrape-only sites.

*Aggregator news + sentiment APIs:*
| Source | Free/Paid | API + key? | History | Real-time? | Coverage | Note |
|---|---|---|---|---|---|---|
| **Marketaux** ⭐ | Free 100/day; ~$30+/mo | REST, key | multi-yr (paid) | near-RT | Global incl. **Tadawul+EGX tagged** | Per-entity sentiment + ticker tagging; free redistribution limited |
| **Finnhub** | Free (60/min) | REST + **WS** | several yr | RT | US broad | Free news + the EPS-surprise feed (see Cat-4) |
| **NewsData.io** | Free 200/day (12h delay) | REST, key | **8 yr archive** | RT (paid) | Global, **Arabic/MENA** | Sentiment/tags on Pro+ |
| **Event Registry (NewsAPI.ai)** | Free dev tier; paid | REST, key | multi-yr | RT | Global | **Event-clustering** (dedupes a story → one event — fits our event model) |
| **Tiingo News** | Paid add-on (~$10–30/mo) | REST, key | **70M-article archive** | RT | US-strong | The backtesting-archive unlock (T2) |
| **Webz.io** | Paid (enterprise) | REST + feeds | deep bulk | RT | Global incl. Arabic | Deep historical backfill (T2) |

*Official primary sources — machine-readable (the highest-trust news):*
| Source | Free? | Feed | Coverage | Note |
|---|---|---|---|---|
| **SEC EDGAR RSS** (8-K/filings) | Free, no key | RSS/Atom + JSON | US issuers | <1s on filing; cleanest free primary event feed |
| **US Federal Reserve** | Free, no key | RSS/XML | US macro | Press releases, FOMC, speeches (verified live 2026-06-07) |
| **ECB** | Free, no key | RSS + **SDMX REST** | Euro/global macro | RSS news + SDMX data |
| **SAMA (Saudi)** | Free | ⚠️ HTML page — **no confirmed RSS/API** | Saudi | Rate decisions/circulars — scrape+sanitize or via aggregator |
| **CBE (Egypt)** | Free | ⚠️ HTML — **no confirmed feed** | Egypt | Same handling as SAMA |
| **Tadawul/Efsah disclosures** | Free read | ⚠️ HTML portal (bilingual AR/EN since 2021) — **no native API** | Saudi | Bridge via **SAHMK** + **Twelve Data `/press_releases` (XSAU)** |
| **EGX/FRA disclosures** | Free read | ⚠️ HTML — **no native API** | Egypt | **Weakest link** — bridge via EODHD + Marketaux EGX tagging |

**News quorum:** US event = **SEC 8-K RSS × Marketaux/GDELT**; US macro = **Fed RSS × ECB RSS**; **Saudi event =
SAHMK × Twelve Data `/press_releases`** (+ Marketaux as third). **MENA caveat:** no Saudi/Egypt government or
exchange exposes a clean news API — route all MENA disclosures through licensed third-party APIs behind the
structured-event firewall; never feed the raw HTML portal to the LLM.

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
- **Verification status (updated 2026-06-07).** First pass (06-06) confirmed: Sharadar, SEC EDGAR, EODHD, Zoya,
  IdealRatings/FTSE, GDELT, SEC RSS, Benzinga, RavenPack, GPR. **Second pass (06-07) additionally verified live:**
  FMP, Tiingo, Polygon, Marketstack, Norgate, SimFin, Stooq, **SAHMK**, Twelve Data (XSAU/XCAI), Marketaux,
  NewsData.io, Event Registry, **Finnhub** (surprise + WS), Fed/ECB feeds, **CFTC COT**, **Kenneth French / AQR**,
  **CBOE**, FRED stress series, **IMF PortWatch**, EPU, **OFAC + UK Sanctions List**, OpenSanctions, UCDP, IFES
  ElectionGuide, EIA, Trading Economics. **Still "verify before relying":** CRSP, Musaffa, S&P/MSCI/DJ Islamic
  feeds, Kun.pro/StockerAPI (opaque pricing), EGXlytics (new/small), tasi R pkg (likely stale), ICE (enterprise).
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

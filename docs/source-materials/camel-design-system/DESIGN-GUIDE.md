# The Camel — Design System

> **Patient capital. Intelligent action. Governed by evidence.**
> *Safety first. Evidence second. Autonomy last.*

The brand and component system for **The Camel** — a guardrailed, Sharia-compliant
autonomous trader/operator. The product's defining idea is an **inversion of trust**:
the LLM only *proposes*; deterministic machinery it cannot edit — a Constitution, an
Edge-Proof evidence gate, a Budget Kernel, append-only audit logs, a kill switch, and
human approval gates — *decides* what actually happens. **Aggressive inside the rails,
powerless outside them. Autonomy is earned through a paper track record, never granted.**

This repository is the design layer for that product: brand assets, foundational tokens
(color, type, spacing), reusable React primitives, and a high-fidelity recreation of the
read-only **Operator Dashboard**.

---

## Product context

The Camel runs a continuous loop — **Observe → Thesis → Choose → Act → Measure → Learn** —
across two Sharia-compliant arms:

- **Trader Camel** — long-only, whole-share, Sharia-screened markets (no leverage, shorting,
  options, or derivatives — ever).
- **Entrepreneur Camel** — builds and ships compliant AI products under a separate constitution.

It is a **personal, educational decision-support project** for the founder's own capital
(Phase 0 — paper only). The interface surfaces what makes the product different from a
portfolio tracker: **the decisions** — Edge-Proof verdicts and Constitution
rejections-with-reasons — plus the macro regime and the live-money safety posture.

### The flow, in five beats
`LLM proposes · Math tests · Guardrails decide · Humans approve what's risky · Autonomy is earned, not granted`

### Five brand values
**Patience · Endurance · Intelligence · Discipline · Evidence**

---

## Sources (input materials)

This system was built by reading the real product codebase and brand assets. If you have
access, explore them to design with higher fidelity:

- **GitHub — product codebase:** [`ahmedmdesouki-bit/The-Camel`](https://github.com/ahmedmdesouki-bit/The-Camel)
  - `dashboard/generate.py` + `dashboard/snapshot.py` — the **authoritative UI source of truth**
    (the operator dashboard's real markup, palette, and data model). The `operator-dashboard`
    UI kit is a faithful recreation of this view.
  - `README.md`, `docs/CAMEL_BRIEF.md`, `docs/CAMEL_CONSTITUTION.md` — product story, rules, tone.
- **Brand logo system** (uploaded): the Round-2 logo sheet (emblem, app icon, wordmark,
  certification seal) + the bronze-and-malachite seal and pin/app-icon variants. Cropped into
  clean assets under `assets/`.
- Related repos by the same author (not used here, but adjacent): `ahmedmdesouki-bit/ezsoft-next`,
  `ahmedmdesouki-bit/veasty`.

> ⚠️ The reader may not have access to the above — they are recorded for provenance.

---

## CONTENT FUNDAMENTALS — how The Camel writes

The voice is that of a **disciplined, evidence-minded operator** — calm, exact, and quietly
authoritative. It reads like a well-kept ledger, not a pitch deck.

- **Honesty over hype.** Never "this will go up." Instead: sample size, hit-rate, what's priced
  in, counter-signals. Booleans are *real facts*, never a self-scored "8/10". Example label:
  *"Honest booleans — each is a real fact, not a self-scored checkbox."*
- **The rejection is the point.** Blocked actions are first-class, shown with the exact reason
  and the limit that fired. *"These are the verdicts — including the rejections, which are the
  whole point."*
- **Terse, declarative cadence.** Short sentences. Em-dashes and the serial structure of the
  five-beat flow. *"Aggressive inside the rails, powerless outside them."*
- **Casing.** Sentence case for prose. UPPERCASE for system verdicts and states
  (`ALLOWED`, `BLOCKED`, `GREEN`, `HALTED`, `Phase 0`) and for eyebrow/label micro-copy.
  Mono for every figure, ticker, signal, and limit name (`max_single_position`, `n=148`).
- **Perspective.** Third-person about the system ("the Camel cannot change its own rules"),
  imperative in controls ("Approve trade", "Kill switch"). Avoids "I"; "you" only in guidance.
- **No emoji** in product UI. (The legacy Python dashboard used a single 🐫 in its `<h1>`; the
  design system replaces it with the engraved emblem mark.) No exclamation marks.
- **Disclaimers are permanent and plain:** *"Not financial, legal, or Sharia advice."*
- **Vocabulary** to reuse: Constitution, Edge Proof / EdgeReport, guardrail, whitelist, frozen /
  close-only, regime, phase gate, kill switch, ledger, paper, envelope, invalidation point.

---

## VISUAL FOUNDATIONS

The aesthetic is **engraved-seal meets instrument panel**: the gravitas of an old certification
mark (malachite + antique gold on parchment) applied to a precise, data-dense operator view.

- **Color.** Deep malachite **green `#0F3B34`** is the primary; **antique gold `#C9A14A`** is the
  only accent (reserved for emphasis, active states, and focus — never decoration). Surfaces are
  warm **sand/parchment `#F5F1E6`**; text is **charcoal `#262626`**. Markets use an honest pair:
  **up `#1A7F37` / down `#C13C1E`**. Operator health is a four-state signal:
  **GREEN / YELLOW `#9A6700` / RED `#CF222E` / BLACK `#24292F`** (halted/kill-switch).
- **Type.** A three-voice system. **Spectral** (serif) is the brand voice — wordmark, headings,
  and long-form prose; it carries quiet, scholarly authority. **IBM Plex Sans** handles UI
  furniture — uppercase eyebrows, nav, table headers, micro-labels. **IBM Plex Mono** carries
  every number that matters — tickers, money, hit-rates, verdicts, ledger, limit names — with
  `tabular-nums` for column alignment.
- **Spacing & layout.** Calm, document-like rhythm on a **4px grid**. Centered max-width
  container (~1100px). Generous whitespace; data tables are dense but never cramped.
- **Backgrounds.** Mostly flat parchment, occasionally a soft `160°` page gradient
  (`sand-200 → sand-100`). The header and brand panels use a `135°` deep-green gradient
  (`green-800 → green-600`). No imagery wallpaper, no noise textures, no busy patterns — the
  engraved logo marks carry all the ornament.
- **Borders & cards.** Cards are **white, 12px radius, a 1px hairline border (`rgba(38,38,38,.12)`)
  and the faintest lift** (`shadow-sm`). This is an instrument panel — flat and trustworthy, not
  a glossy marketing surface. Radii scale from 4px (chips/inputs) to a 22px app-icon squircle to
  full pills (badges/status).
- **Shadows.** Low and warm, tinted with the green ink (`rgba(15,59,52,.06–.16)`) — never neutral
  grey, never large blurry drop-shadows.
- **Iconography.** Thin-line, 1.5px stroke (see ICONOGRAPHY). Status uses tiny dots and ✓/✕/⛔
  glyphs rather than heavy icons.
- **Motion.** Restrained. A 0.22s ease-out on hovers/tabs; a 0.2s fade on view changes. No bounces,
  no parallax, no infinite loops. `prefers-reduced-motion` collapses everything to near-instant.
- **Hover / press.** Buttons darken on hover (primary → `green-700`) and nudge down ~0.5px +
  go darkest on press (`green-900`). Secondary/ghost get a faint green wash. Table rows get a
  3%-green hover tint. Focus is always the **gold ring** (`0 0 0 3px rgba(201,161,74,.55)`).
- **Transparency & blur.** Used sparingly — translucent gold/green washes for badge fills and the
  nav backdrop. No heavy glassmorphism.
- **Imagery mood.** The logo marks are warm, metallic, antique — bronze, malachite, brushed gold
  on aged parchment. If photography is ever added, keep it warm and earthen, never cold/blue.

---

## ICONOGRAPHY

The Camel uses a **thin-line icon style** (1.5px stroke), matching the engraved, fine-line quality
of the seal and the value glyphs (hourglass · mountain · brain · shield · magnifier).

- **Icon set:** [**Lucide**](https://lucide.dev) (`unpkg.com/lucide`), loaded from CDN. Its
  consistent 1.5px stroke and rounded joins are the closest match to the brand's fine-line marks.
  Use it for all UI icons (refresh, download, check, octagon-x for the kill switch, etc.).
  > ⚠️ **Substitution flag:** the product codebase ships no icon font of its own (the legacy
  > Python dashboard used a lone 🐫 emoji and ✅/⛔ unicode). Lucide is our chosen stand-in — swap
  > for a bespoke set if one is commissioned.
- **Unicode glyphs** are used intentionally for verdicts and gate marks: `✓` (allow/pass),
  `✕` (fail), `⛔` (blocked). These read instantly in dense tables.
- **No emoji** in product surfaces. **No multicolor / filled icon styles.** Keep stroke weight and
  size consistent (16–18px inline, 38px value glyphs).
- **Brand marks** (not icons) live in `assets/`: `emblem.png` (hexagon), `app-icon.png`,
  `wordmark.png`, `seal.png`, plus the original `logo-*` sheets.

---

## VISUAL FOUNDATIONS — at a glance (tokens)

| Concern | Entry file | Highlights |
|---|---|---|
| Color | `tokens/colors.css` | green/gold/sand/ink scales · up/down · 4-state signal · semantic aliases |
| Type | `tokens/typography.css` | Spectral / IBM Plex Sans / IBM Plex Mono · scale · tracking |
| Spacing | `tokens/spacing.css` | 4px scale · radii · warm shadows · borders · motion |
| Fonts | `tokens/fonts.css` | Google Fonts `@import` (substitution — see below) |
| Base | `tokens/base.css` | element defaults + `.cml-*` utilities |

> ⚠️ **Font substitution:** the product renders in system serifs (Iowan Old Style / Georgia) to
> stay offline. The design system substitutes **Spectral**, **IBM Plex Sans**, and **IBM Plex Mono**
> (nearest Google-Fonts matches, loaded via CDN `@import`). **If you have licensed binaries for the
> exact wordmark face, drop them in and add `@font-face` rules** — and let us know so we can update.

---

## INDEX — what's in this system

**Root**
- `styles.css` — the single entry point consumers link (imports only).
- `readme.md` — this guide.
- `SKILL.md` — Agent-Skill front-matter for use in Claude Code.

**`tokens/`** — `colors.css`, `typography.css`, `spacing.css`, `fonts.css`, `base.css`.

**`assets/`** — brand marks: `emblem.png`, `app-icon.png`, `wordmark.png`, `seal.png`,
`logo-brandsheet.png`, `logo-bronze-seal.png`, `logo-variants.png`.

**`guidelines/`** — 19 foundation specimen cards (the Design System tab): Colors (6),
Type (5), Spacing (3), Brand (5).

**`components/`** — reusable React primitives (`window.TheCamelDesignSystem_fdd784`):
| Group | Components |
|---|---|
| `core/` | `Button`, `IconButton`, `Card` |
| `feedback/` | `Badge`, `StatusPill`, `Verdict` |
| `data/` | `StatCard`, `GateList` |
| `forms/` | `Input`, `Toggle` |
| `navigation/` | `Tabs` |

Each component has a `.jsx` (implementation), `.d.ts` (props), `.prompt.md` (usage), and a
`@dsCard` HTML in its directory. Shared class styles live in `components/components.css`.

**`ui_kits/operator-dashboard/`** — high-fidelity, interactive recreation of the read-only
Operator Dashboard (Overview · Portfolio · Decisions · Regime · Sharia · Ops, plus a working
kill-switch toggle). Faithful to `dashboard/generate.py`. Files: `index.html`, `data.js`,
`views.jsx`, `Dashboard.jsx`, `README.md`.

---

## Using the system

Consumers link one file:

```html
<link rel="stylesheet" href="styles.css">
```

Components are exposed on `window.TheCamelDesignSystem_fdd784` after loading `_ds_bundle.js`
(auto-generated). In an `@dsCard` / kit HTML:

```html
<script src="../../_ds_bundle.js"></script>
<script type="text/babel">
  const { Button, Card, StatCard, Verdict } = window.TheCamelDesignSystem_fdd784;
</script>
```

Reference design values through the CSS custom properties (`var(--green-800)`, `var(--font-mono)`,
`var(--radius-lg)`) — never hard-code hexes.

# The Camel — Design System · Claude Code handoff

This bundle is a **complete, self-contained design system** for **The Camel** (a guardrailed,
Sharia-compliant autonomous trader/operator). It is structured to be used directly inside
**Claude Code** as an Agent Skill or as a plain reference.

---

## What's in the box

| Path | What it is |
|---|---|
| `SKILL.md` | Agent-Skill front-matter. Drop this folder into `.claude/skills/the-camel-design/` and invoke it. |
| `readme.md` | **The design guide** — brand story, content fundamentals, visual foundations, iconography, full token + component index. Read this first. |
| `styles.css` | The single CSS entry point. Link this one file; it `@import`s everything (tokens + fonts + base + component classes). |
| `tokens/` | CSS custom properties — `colors.css`, `typography.css`, `spacing.css`, `fonts.css`, `base.css`. |
| `components/` | Reusable **React** primitives (plain JSX, React-only — no other deps). Each has `.jsx` + `.d.ts` (props) + `.prompt.md` (usage) + a demo `.card.html`. Shared styling in `components/components.css`. |
| `ui_kits/operator-dashboard/` | A high-fidelity, interactive recreation of the read-only operator view — the reference for "what a real screen looks like." |
| `assets/` | Brand marks as **transparent PNGs**: `emblem.png`, `app-icon.png`, `seal.png`, `wordmark.png` (+ original source sheets). |
| `guidelines/` | Foundation specimen cards (visual reference for tokens). |

---

## How to use it in a real codebase

> The HTML files (`*.card.html`, the UI kit `index.html`) are **design references / prototypes** —
> they show the intended look and behavior. Recreate them in your target environment (React, Vue,
> SwiftUI, etc.) using its established patterns. Don't ship the prototype HTML directly.

**Fidelity: high.** Colors, type, spacing, and component states are final — match them exactly.

### 1. Tokens (any framework)
Link or port `styles.css`. Reference everything through the CSS custom properties — never hard-code
hexes:
```css
color: var(--text-body);
background: var(--surface-card);
border: 1px solid var(--line);
border-radius: var(--radius-lg);
font-family: var(--font-mono);   /* figures/tickers always mono */
```

### 2. Components (React)
The components in `components/**/*.jsx` are **plain React** (import React only) and style themselves
via the `.cml-*` classes in `components/components.css`. In a React app you can import them directly:
```jsx
import { Button } from "./components/core/Button.jsx";
import { StatCard } from "./components/data/StatCard.jsx";
// ...ensure styles.css (which includes components.css) is loaded globally.
```
Each component's `.d.ts` is the props contract and its `.prompt.md` has a copy-paste example.

> ⚠️ **No build step needed for the tokens/CSS.** The `_ds_bundle.js` referenced inside the
> `*.card.html` files is a **platform-generated artifact** that does NOT exist in this bundle —
> it only exists in the design tool. In your codebase, import the `.jsx` source directly (above)
> instead of loading a bundle. The card HTML files are previews, not production wiring.

### 3. Fonts
`tokens/fonts.css` loads **Spectral**, **IBM Plex Sans**, and **IBM Plex Mono** from Google Fonts.
These are **nearest-match substitutes** — the product's own renderer uses system serifs and there is
no licensed wordmark binary in this bundle. Swap in real `@font-face` files if/when you have them.

### 4. Icons
UI icons are **Lucide** (`lucide` on npm / CDN), thin 1.5px stroke. Verdict/gate glyphs use unicode
(`✓ ✕ ⛔`). No emoji in product surfaces.

---

## The three things that define the look

1. **Engraved-seal meets instrument panel** — deep malachite green `#0F3B34` + antique gold `#C9A14A`
   on warm parchment `#F5F1E6`, charcoal text `#262626`. Gold is an accent only.
2. **Three type voices** — Spectral (serif prose/headings) · IBM Plex Sans (UI labels) ·
   IBM Plex Mono (every figure).
3. **Honest, evidence-minded tone** — the rejection is the point; booleans are real facts; figures
   are mono. See `readme.md` → CONTENT FUNDAMENTALS.

---

## Provenance
Built from the real product codebase: **`github.com/ahmedmdesouki-bit/The-Camel`**
(`dashboard/generate.py` + `dashboard/snapshot.py` are the authoritative UI source). Explore that
repo for deeper context on the operator dashboard and the Constitution/Edge-Proof model.

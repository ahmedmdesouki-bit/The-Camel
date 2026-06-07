# Operator Dashboard — UI kit

A high-fidelity, interactive recreation of **The Camel's read-only operator view**, faithful to
the product's real renderer (`dashboard/generate.py` + `dashboard/snapshot.py` in
[`ahmedmdesouki-bit/The-Camel`](https://github.com/ahmedmdesouki-bit/The-Camel)).

It is **read-only by design** — there is no order entry. The view surfaces the *decisions*
(Edge-Proof verdicts and Constitution rejections-with-reasons), the macro regime, the Sharia
whitelist, the ledger, and the live-money safety posture — not just holdings.

## Screens (tabs)
- **Overview** — KPI tiles + the honest live-money safety posture (`GateList`).
- **Portfolio** — the whole-share, Sharia-screened positions table with allocation bars.
- **Decisions** — Edge-Proof verdicts and guardrail events (the rejections are the point).
- **Regime** — current 10-state macro regime + history.
- **Sharia** — the whitelist; frozen names are close-only.
- **Ops** — recent loop runs, the hash-chain ledger, and health checks.

## Interactions
- Tab navigation (`Tabs`) switches views.
- The header **Kill switch** toggles a HALTED (BLACK) state, banner, and status pill — a
  demonstration of the system's defining control.

## Composition
Built almost entirely from the design-system primitives — `Card`, `StatCard`, `GateList`,
`Badge`, `StatusPill`, `Verdict`, `Tabs`. Only the data tables, regime panel, and header are
kit-local (styled in `index.html`).

## Files
- `index.html` — the entire kit: shell styles, the snapshot data, the six views, the app shell,
  and the root render are all **inline** (the `@startingPoint` tag is on line 2).

> Everything is inlined on purpose. The platform compiler bundles every standalone `.js`/`.jsx`
> file into the shared `_ds_bundle.js`; a kit app-entry with a top-level
> `ReactDOM.createRoot(...).render()` must therefore live in **inline `<script>` blocks** (which are
> never bundled) so it can't hijack a consumer's `#root`. Only the reusable primitives in
> `components/**/*.jsx` belong in the bundle.

> Static snapshot · no live fetch · paper only. Not financial, legal, or Sharia advice.

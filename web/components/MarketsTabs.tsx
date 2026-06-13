"use client";
// MarketsTabs (S-UI) — a self-contained tabbed panel for the operator window: Market / Watchlist / Hotlist.
// Reads the published snapshot blocks (state.market / state.watchlist / state.hotlist) — REAL ingested numbers,
// never mock data. Styled with the same Camel Design System classes the rest of the window already uses
// (k-table, cml-tick, k-fig, cml-badge, up/down). Tab switching is the only client interaction; the data is SSR.
import { useState } from "react";
import type { MarketBlock, PriceRow, HotList } from "@/lib/types";

const px = (n: number | null | undefined) => (n == null ? "—" : Number(n).toFixed(2));
const pct = (n: number | null | undefined) =>
  n == null ? "—" : `${n > 0 ? "+" : ""}${Number(n).toFixed(2)}%`;
const dir = (n: number | null | undefined) => (n == null ? "" : n > 0 ? "up" : n < 0 ? "down" : "");
const shariaTone = (s: string | null | undefined) =>
  s === "compliant" || s === "pass" ? "green" : s === "doubtful" ? "gold" : s === "frozen" || s === "fail" ? "red" : "neutral";

function PriceTable({ rows, withNote = false }: { rows: PriceRow[]; withNote?: boolean }) {
  if (!rows?.length) return <p className="k-empty">Nothing to show yet — waiting on the next data ingest.</p>;
  return (
    <table className="k-table">
      <thead>
        <tr>
          <th>Symbol</th>
          {withNote && <th>Name</th>}
          <th>Last</th>
          <th>1-day</th>
          <th>~1-month</th>
          <th>Sharia</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={`${r.symbol}-${r.note ?? ""}`}>
            <td className="cml-tick">{r.symbol}</td>
            {withNote && <td className="k-mono-sm">{r.note || "—"}</td>}
            <td className="k-fig">{px(r.last)}</td>
            <td className={`k-fig ${dir(r.change_1d_pct)}`}>{pct(r.change_1d_pct)}</td>
            <td className={`k-fig ${dir(r.change_21d_pct)}`}>{pct(r.change_21d_pct)}</td>
            <td>
              <span className={`cml-badge cml-badge--${shariaTone(r.sharia_status)}`}>
                {r.sharia_status || "—"}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function MarketsTabs({
  market,
  watchlist,
  hotlist,
}: {
  market?: MarketBlock;
  watchlist?: PriceRow[];
  hotlist?: HotList;
}) {
  const [tab, setTab] = useState<"market" | "watchlist" | "hotlist">("market");

  const TabBtn = ({ id, label }: { id: typeof tab; label: string }) => {
    const active = tab === id;
    return (
      <button
        type="button"
        onClick={() => setTab(id)}
        aria-pressed={active}
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: "6px 16px",
          fontFamily: "var(--font-sans, system-ui, sans-serif)",
          fontSize: 13,
          letterSpacing: "0.02em",
          color: active ? "var(--green-800, #0f3b34)" : "var(--ink-soft, #6b7a76)",
          borderBottom: active ? "2px solid var(--gold-500, #c9a14a)" : "2px solid transparent",
          fontWeight: active ? 700 : 500,
        }}
      >
        {label}
      </button>
    );
  };

  return (
    <div>
      <div
        role="tablist"
        style={{ display: "flex", gap: 4, borderBottom: "1px solid var(--line, #e5ded0)", marginBottom: 14 }}
      >
        <TabBtn id="market" label="Market" />
        <TabBtn id="watchlist" label="Watchlist" />
        <TabBtn id="hotlist" label="Hotlist" />
      </div>

      {tab === "market" && (
        <div>
          <p className="cml-card__hint" style={{ marginTop: 0 }}>
            Macro — the real market state (FRED + the engine&rsquo;s regime).
          </p>
          {market?.macro?.length ? (
            <table className="k-table">
              <thead>
                <tr>
                  <th>Indicator</th>
                  <th>Latest</th>
                  <th>As of</th>
                </tr>
              </thead>
              <tbody>
                {market.macro.map((m, i) => (
                  <tr key={i}>
                    <td>{m.label}</td>
                    <td className="k-fig">{m.value == null ? "—" : m.value}</td>
                    <td className="k-mono-sm">{m.as_of || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="k-empty">No macro data published yet.</p>
          )}
          {market?.regime && (
            <p className="cml-card__hint" style={{ marginTop: 10 }}>
              Regime: <strong style={{ color: "var(--green-800, #0f3b34)" }}>{market.regime.regime}</strong>
              {market.regime.confidence != null && ` · confidence ${Math.round(market.regime.confidence * 100)}%`}
            </p>
          )}
          <p className="cml-card__hint" style={{ marginTop: 14 }}>
            Compliant universe — real prices as of the last ingest.
          </p>
          <PriceTable rows={market?.universe ?? []} />
        </div>
      )}

      {tab === "watchlist" && (
        <div>
          <p className="cml-card__hint" style={{ marginTop: 0 }}>
            Names being tracked. Tracking only — being here is <em>not</em> the tradeable whitelist.
          </p>
          <PriceTable rows={watchlist ?? []} withNote />
        </div>
      )}

      {tab === "hotlist" && (
        <div>
          <p className="cml-card__hint" style={{ marginTop: 0 }}>
            Pinned — high-conviction names.
          </p>
          <PriceTable rows={hotlist?.pinned ?? []} withNote />
          <p className="cml-card__hint" style={{ marginTop: 14 }}>
            Movers — the biggest 1-day moves in the tracked set.
          </p>
          <PriceTable rows={hotlist?.movers ?? []} />
        </div>
      )}
    </div>
  );
}

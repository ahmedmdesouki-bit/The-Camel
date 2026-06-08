import type { EquityPoint } from "@/lib/types";

// Pure-SVG equity curve (no chart library) in the Camel palette. Renders the paper track record:
// total value over time, with an antique-gold line over a malachite-tinted area.
export default function EquityChart({ points }: { points: EquityPoint[] }) {
  const series = points
    .map((p) => (p.total_value == null ? null : Number(p.total_value)))
    .filter((v): v is number => v != null && Number.isFinite(v));

  if (series.length < 2) {
    return <p className="k-empty">Not enough history yet — the curve fills in as the publisher runs.</p>;
  }

  const W = 720, H = 180, PAD = 8;
  const min = Math.min(...series), max = Math.max(...series);
  const span = max - min || 1;
  const x = (i: number) => PAD + (i / (series.length - 1)) * (W - 2 * PAD);
  const y = (v: number) => PAD + (1 - (v - min) / span) * (H - 2 * PAD);

  const line = series.map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const area = `${line} L${x(series.length - 1).toFixed(1)},${H - PAD} L${x(0).toFixed(1)},${H - PAD} Z`;

  const first = series[0], last = series[series.length - 1];
  const chg = first ? ((last - first) / first) * 100 : 0;
  const chgCls = chg > 0 ? "up" : chg < 0 ? "down" : "";

  return (
    <div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 6 }}>
        <span className="cml-stat__value" style={{ fontSize: "var(--text-2xl)" }}>
          ${last.toLocaleString("en-US", { maximumFractionDigits: 0 })}
        </span>
        <span className={`k-fig ${chgCls}`}>{chg >= 0 ? "+" : ""}{chg.toFixed(2)}% over {series.length} points</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="180" preserveAspectRatio="none" role="img"
        aria-label={`Paper equity curve, ${chg.toFixed(1)} percent over the recorded period`}>
        <defs>
          <linearGradient id="cml-eq" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(15,59,52,0.22)" />
            <stop offset="100%" stopColor="rgba(15,59,52,0.02)" />
          </linearGradient>
        </defs>
        <path d={area} fill="url(#cml-eq)" />
        <path d={line} fill="none" stroke="var(--gold-500)" strokeWidth="2"
          strokeLinejoin="round" strokeLinecap="round" />
      </svg>
    </div>
  );
}

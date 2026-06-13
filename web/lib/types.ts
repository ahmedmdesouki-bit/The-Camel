// Mirrors dashboard/snapshot.py::build_snapshot() — the single state contract the Python brain publishes.

export interface Kpis {
  cash: number; positions_value: number; total_value: number;
  unrealized_pnl: number; realized_pnl: number; cash_drag_pct: number; open_positions: number;
}
export interface GateItem { label: string; ok: boolean; }
export interface Governance {
  phase: number; phase_label: string; kill_switch: string;
  allow_leverage: boolean; require_approval_live: boolean;
  live_at_risk: number; paper_at_risk: number;
  gate_items: GateItem[]; gate_passed: number; gate_total: number;
}
// NB: numeric fields are `number | null` — the Python snapshot emits null when a SQLite column / JSON key
// is missing (build_snapshot in dashboard/snapshot.py), and the render helpers below treat null as "—".
export interface Position {
  symbol: string; qty: number | null; avg_cost: number | null; market_price: number | null;
  market_value: number | null; unrealized_pnl: number | null; realized_pnl: number | null; status: string;
}
export interface LedgerRow { ts: string; type: string; symbol: string; amount: number | null; balance_after: number | null; }
export interface Rejection { ts: string; blocked: boolean; symbol: string; reason: string; limit_hit: string; }
export interface EdgeDecision {
  ts: string; symbol: string; signal: string; trade_allowed: boolean; reason: string;
  sample_size: number | null; hit_rate: number | null; median_forward_return: number | null;
  benchmark_excess_return: number | null; confidence: number | null;
}
export interface Regime { classified_at: string; regime: string; confidence: number | null; signals: string[]; }
export interface WhitelistRow { symbol: string; sharia_status: string; frozen: boolean; }
// S17.7 — the Kitchen
export interface DeskStatus {
  desk_id: string; status: string; summary: string; ts: string | null; evidence_n: number; paused: boolean;
}
export interface BoardRow {
  id: number; symbol: string; action: string; score: number | null; regime: string;
  sharia_status: string; edge_allowed: boolean; hit_rate: number | null; confidence: number | null;
  recommended_action: string; invalidation: string; reason_chain: string[];
}

// S-UI — Market / Watchlist / Hotlist (real ingested numbers; numeric fields null when no data)
export interface MacroRow { label: string; value: number | null; as_of: string | null; }
export interface PriceRow {
  symbol: string; last: number | null; date?: string | null;
  change_1d_pct: number | null; change_21d_pct: number | null; sharia_status: string; note?: string;
}
export interface MarketBlock { macro: MacroRow[]; regime: Regime | null; universe: PriceRow[]; }
export interface HotList { pinned: PriceRow[]; movers: PriceRow[]; }

export interface Snapshot {
  mode: string;
  health: { status: string; issues: string[]; checks: Record<string, string> };
  kpis: Kpis;
  governance: Governance;
  positions: Position[];
  ledger: LedgerRow[];
  runs: { id: number; started_at: string; ended_at: string; phase: number; outcome: string }[];
  guardrail: Rejection[];
  edge_decisions: EdgeDecision[];
  regime: Regime | null;
  regime_history: { classified_at: string; regime: string; confidence: number | null }[];
  whitelist: WhitelistRow[];
  desks?: DeskStatus[];     // S17.7 — the Kitchen (optional: older snapshots predate it)
  board?: BoardRow[];       // S17.7 — the Opportunity Board
  market?: MarketBlock;     // S-UI — real market numbers (FRED macro + regime + compliant universe)
  watchlist?: PriceRow[];   // S-UI — founder-curated tracking list + live numbers
  hotlist?: HotList;        // S-UI — pinned hot names + computed movers
}

export interface SystemStateRow { id: number; state: Snapshot; updated_at: string; }

export interface EquityPoint { ts: string; total_value: number | null; cash: number | null; positions_value: number | null; }

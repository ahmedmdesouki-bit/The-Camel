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
export interface Position {
  symbol: string; qty: number; avg_cost: number; market_price: number; market_value: number;
  unrealized_pnl: number; realized_pnl: number; status: string;
}
export interface LedgerRow { ts: string; type: string; symbol: string; amount: number; balance_after: number; }
export interface Rejection { ts: string; blocked: boolean; symbol: string; reason: string; limit_hit: string; }
export interface EdgeDecision {
  ts: string; symbol: string; signal: string; trade_allowed: boolean; reason: string;
  sample_size: number; hit_rate: number; median_forward_return: number;
  benchmark_excess_return: number; confidence: number;
}
export interface Regime { classified_at: string; regime: string; confidence: number; signals: string[]; }
export interface WhitelistRow { symbol: string; sharia_status: string; frozen: boolean; }

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
  regime_history: { classified_at: string; regime: string; confidence: number }[];
  whitelist: WhitelistRow[];
}

export interface SystemStateRow { id: number; state: Snapshot; updated_at: string; }

export interface EquityPoint { ts: string; total_value: number | null; cash: number | null; positions_value: number | null; }

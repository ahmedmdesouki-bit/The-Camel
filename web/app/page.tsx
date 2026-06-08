import { createClient } from "@/lib/supabase/server";
import { getLatestSnapshot, getEquityPoints, isAllowed } from "@/lib/data";
import SignOut from "@/components/SignOut";
import ControlBar from "@/components/ControlBar";
import EquityChart from "@/components/EquityChart";
import LiveRefresh from "@/components/LiveRefresh";
import type { Snapshot, EquityPoint } from "@/lib/types";

export const dynamic = "force-dynamic"; // always read the freshest published state

const money = (n: number | null | undefined) =>
  n == null ? "—" : `$${Number(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const pnlClass = (n: number | null | undefined) => (n == null ? "" : n > 0 ? "up" : n < 0 ? "down" : "");

export default async function Page() {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  const email = user?.email ?? null;

  if (!isAllowed(email)) {
    return (
      <div className="k-login">
        <h1>Not on the guest list</h1>
        <p>{email} isn’t authorized for this private window. Ask the founder to add you.</p>
        <SignOut />
      </div>
    );
  }

  const { snapshot, updatedAt } = await getLatestSnapshot();
  const equity = await getEquityPoints();

  return (
    <main className="k-app">
      <LiveRefresh />
      <header className="k-header">
        <div className="k-brand">
          <div className="k-seal">C</div>
          <div>
            <h1 className="k-title">The Camel</h1>
            <div className="k-tag">OPERATOR WINDOW · PAPER ONLY · READ-ONLY MIRROR</div>
          </div>
        </div>
        <div className="k-userbox">
          <span>{email}</span>
          <SignOut />
        </div>
      </header>

      {snapshot ? <Dashboard snapshot={snapshot} updatedAt={updatedAt} email={email} equity={equity} /> : <Empty />}

      <div className="k-seal-rule" />
      <footer className="k-footer">
        The Camel · a guardrailed, Sharia-compliant operator · this window is a read-only mirror of a
        paper-mode system. No real capital is at risk.
      </footer>
    </main>
  );
}

function Empty() {
  return (
    <div className="k-grid" style={{ marginTop: 20 }}>
      <div className="col-12">
        <div className="cml-card">
          <div className="cml-card__body">
            <p className="k-empty">
              No system state has been published yet. Run the publisher on the brain side:
              <code className="k-chip" style={{ marginLeft: 8 }}>python -m ops.publish_state</code>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function Card({ title, hint, children, col = 12 }: { title: string; hint?: string; children: React.ReactNode; col?: number }) {
  return (
    <div className={`col-${col}`}>
      <div className="cml-card">
        <div className="cml-card__head">
          <h2 className="cml-card__title">{title}</h2>
          {hint && <p className="cml-card__hint">{hint}</p>}
        </div>
        <div className="cml-card__body">{children}</div>
      </div>
    </div>
  );
}

function Dashboard({ snapshot: s, updatedAt, email, equity }: { snapshot: Snapshot; updatedAt: string | null; email: string | null; equity: EquityPoint[] }) {
  const k = s.kpis;
  const g = s.governance;
  return (
    <>
      <div className="k-status">
        <span className={`cml-status cml-status--${s.health.status}`}>{s.health.status}</span>
        <span className="k-statusmeta">{g.phase_label} · mode {s.mode}</span>
        {g.kill_switch === "HALTED" && <span className="k-kill">● KILL SWITCH HALTED</span>}
        <span className="k-statusmeta" style={{ marginLeft: "auto" }}>
          updated {updatedAt ? new Date(updatedAt).toLocaleString() : "—"}
        </span>
      </div>

      <div className="k-grid">
        {/* Equity curve (paper track record) */}
        <Card title="Paper equity curve" hint="Total portfolio value over time — virtual money, recorded each publish." col={12}>
          <EquityChart points={equity} />
        </Card>

        {/* KPIs */}
        <Card title="Portfolio" hint="Paper book — virtual money only." col={8}>
          <div className="cml-statgrid">
            <Stat label="Total value" value={money(k.total_value)} />
            <Stat label="Cash" value={money(k.cash)} sub={`${k.cash_drag_pct}% drag`} />
            <Stat label="Positions" value={money(k.positions_value)} sub={`${k.open_positions} open`} />
            <Stat label="Unrealized P&L" value={money(k.unrealized_pnl)} cls={pnlClass(k.unrealized_pnl)} />
            <Stat label="Realized P&L" value={money(k.realized_pnl)} cls={pnlClass(k.realized_pnl)} />
            <Stat label="Live at risk" value={money(g.live_at_risk)} sub="always $0 in paper" />
          </div>
        </Card>

        {/* Regime */}
        <Card title="Market regime" hint="The macro state the engine classified." col={4}>
          {s.regime ? (
            <>
              <div className="k-regime-val">{s.regime.regime}</div>
              <div className="k-regime-conf">confidence {Math.round((s.regime.confidence ?? 0) * 100)}%</div>
              <div style={{ marginTop: 8 }}>
                {(s.regime.signals ?? []).slice(0, 6).map((sig, i) => (
                  <span className="k-chip" key={i}>{sig}</span>
                ))}
              </div>
            </>
          ) : (
            <p className="k-empty">No regime classified yet (needs macro data).</p>
          )}
        </Card>

        {/* Governance gate */}
        <Card title="Safety posture" hint={`${g.gate_passed}/${g.gate_total} guardrails confirmed — each item is a real boolean fact, not a score.`} col={6}>
          {g.gate_items.map((it, i) => (
            <div className="cml-gate__item" key={i}>
              <span className={`cml-gate__mark cml-gate__mark--${it.ok ? "ok" : "no"}`}
                role="img" aria-label={it.ok ? "confirmed" : "failed"}>{it.ok ? "✓" : "✕"}</span>
              {it.label}
            </div>
          ))}
        </Card>

        {/* Positions */}
        <Card title="Positions" col={6}>
          {s.positions.filter((p) => (p.status || "open") === "open").length ? (
            <table className="k-table">
              <thead><tr><th>Symbol</th><th>Qty</th><th>Avg cost</th><th>Mkt value</th><th>Unreal.</th></tr></thead>
              <tbody>
                {s.positions.filter((p) => (p.status || "open") === "open").map((p) => (
                  <tr key={p.symbol}>
                    <td className="cml-tick">{p.symbol}</td>
                    <td className="k-fig">{p.qty}</td>
                    <td className="k-fig">{money(p.avg_cost)}</td>
                    <td className="k-fig">{money(p.market_value)}</td>
                    <td className={`k-fig ${pnlClass(p.unrealized_pnl)}`}>{money(p.unrealized_pnl)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="k-empty">No open positions.</p>}
        </Card>

        {/* Edge decisions — the whole point */}
        <Card title="Edge Proof verdicts" hint="Why the system did or didn’t trade — the evidence gate, not just holdings." col={12}>
          {s.edge_decisions.length ? (
            <table className="k-table">
              <thead><tr><th>Symbol</th><th>Signal</th><th>Verdict</th><th>n</th><th>Hit</th><th>Excess</th><th>Reason</th></tr></thead>
              <tbody>
                {s.edge_decisions.map((e, i) => (
                  <tr key={i}>
                    <td className="cml-tick">{e.symbol}</td>
                    <td className="k-mono-sm">{e.signal}</td>
                    <td><span className={`cml-verdict cml-verdict--${e.trade_allowed ? "ok" : "no"}`}>{e.trade_allowed ? "● EDGE" : "○ NO EDGE"}</span></td>
                    <td className="k-fig">{e.sample_size ?? "—"}</td>
                    <td className="k-fig">{e.hit_rate ?? "—"}</td>
                    <td className={`k-fig ${pnlClass(e.benchmark_excess_return)}`}>{e.benchmark_excess_return ?? "—"}</td>
                    <td className="k-mono-sm">{e.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="k-empty">No Edge Proof decisions logged yet.</p>}
        </Card>

        {/* Rejections */}
        <Card title="Guardrail decisions" hint="Constitution rejections, with reasons." col={6}>
          {s.guardrail.length ? (
            <table className="k-table">
              <thead><tr><th><span className="sr-only">State</span></th><th>Symbol</th><th>Reason</th><th>Limit</th></tr></thead>
              <tbody>
                {s.guardrail.slice(0, 12).map((r, i) => (
                  <tr key={i}>
                    <td>{r.blocked ? <span className="cml-badge cml-badge--red">blocked</span> : <span className="cml-badge cml-badge--green">allowed</span>}</td>
                    <td className="cml-tick">{r.symbol || "—"}</td>
                    <td className="k-mono-sm">{r.reason}</td>
                    <td><code className="k-chip">{r.limit_hit || "—"}</code></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="k-empty">No guardrail events yet.</p>}
        </Card>

        {/* Ledger */}
        <Card title="Ledger (recent)" hint="Append-only, hash-chained." col={6}>
          {s.ledger.length ? (
            <table className="k-table">
              <thead><tr><th>Type</th><th>Symbol</th><th>Amount</th><th>Balance</th></tr></thead>
              <tbody>
                {s.ledger.slice(0, 12).map((l, i) => (
                  <tr key={i}>
                    <td><span className="cml-badge cml-badge--neutral">{l.type}</span></td>
                    <td className="cml-tick">{l.symbol || "—"}</td>
                    <td className={`k-fig ${pnlClass(l.amount)}`}>{money(l.amount)}</td>
                    <td className="k-fig">{money(l.balance_after)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="k-empty">No ledger entries yet.</p>}
        </Card>

        {/* Sharia whitelist */}
        <Card title="Sharia whitelist" hint="Compliant universe + watch/freeze status." col={6}>
          {s.whitelist.length ? (
            <table className="k-table">
              <thead><tr><th>Symbol</th><th>Status</th><th>Frozen</th></tr></thead>
              <tbody>
                {s.whitelist.map((w) => (
                  <tr key={w.symbol}>
                    <td className="cml-tick">{w.symbol}</td>
                    <td>
                      <span className={`cml-badge cml-badge--${w.sharia_status === "compliant" ? "green" : w.sharia_status === "doubtful" ? "gold" : "red"}`}>
                        {w.sharia_status}
                      </span>
                    </td>
                    <td>{w.frozen ? <span className="cml-badge cml-badge--red">frozen</span> : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="k-empty">Whitelist empty.</p>}
        </Card>

        {/* Control bar (interactive — phase 2; queues commands the brain executes) */}
        <Card title="Controls" hint="Commands are QUEUED here and executed by the brain on its next poll — nothing runs in the browser. Paper only." col={6}>
          <ControlBar phase={g.phase} email={email} />
        </Card>
      </div>
    </>
  );
}

function Stat({ label, value, sub, cls }: { label: string; value: string; sub?: string; cls?: string }) {
  return (
    <div>
      <div className="cml-stat__label">{label}</div>
      <div className={`cml-stat__value ${cls ?? ""}`}>{value}</div>
      {sub && <div className="cml-stat__sub">{sub}</div>}
    </div>
  );
}

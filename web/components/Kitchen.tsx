"use client";
import { useState } from "react";
import type { DeskStatus, BoardRow } from "@/lib/types";

// S17.7 — The Kitchen: watch the desks work and steer the Opportunity Board. Every control is a REQUEST
// queued into Supabase `commands` (via /api/command); the brain (ops/command_poller.py) validates it as
// founder-only and acts on its next poll. Nothing runs in the browser, nothing here moves money — acting
// on an approved proposal still flows through the full Edge Proof → Constitution → Budget → Approval gate.

const DESK_BLURB: Record<string, string> = {
  scout: "finds data", herald: "gathers news", oracle: "reads the regime",
  mufti: "Sharia compliance", quant: "the edge", steward: "the portfolio", conductor: "the decision",
};

async function queue(type: string, payload: Record<string, unknown>): Promise<{ ok: boolean; text: string }> {
  try {
    const res = await fetch("/api/command", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, payload }),
    });
    const json = await res.json();
    return res.ok ? { ok: true, text: `queued: ${type}` } : { ok: false, text: json.error || "failed" };
  } catch (e) {
    return { ok: false, text: String(e) };
  }
}

export default function Kitchen({ desks, board }: { desks: DeskStatus[]; board: BoardRow[] }) {
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function act(type: string, payload: Record<string, unknown>) {
    setBusy(true); setMsg(null);
    setMsg(await queue(type, payload));
    setBusy(false);
  }

  return (
    <div>
      {msg && <p className={`cml-note ${msg.ok ? "cml-ok" : "cml-err"}`}>{msg.text}</p>}

      {/* The desks — the workforce at a glance */}
      <h3 className="k-subhead">The desks</h3>
      <div className="k-deskgrid">
        {desks.length === 0 && <p className="k-empty">No desk runs yet. Run a cycle on the brain: <code className="k-chip">python -m research.workforce cycle</code></p>}
        {desks.map((d) => (
          <div className={`k-desk k-desk--${d.paused ? "paused" : d.status}`} key={d.desk_id}>
            <div className="k-desk__top">
              <span className="k-desk__name">{d.desk_id.toUpperCase()}</span>
              <span className={`cml-badge cml-badge--${d.paused ? "gold" : d.status === "ok" ? "green" : d.status === "error" ? "red" : "neutral"}`}>
                {d.paused ? "paused" : d.status}
              </span>
            </div>
            <div className="k-desk__job">{DESK_BLURB[d.desk_id] ?? ""}</div>
            <div className="k-desk__summary">{d.summary}</div>
            <div className="k-desk__ctl">
              <button className="cml-btn cml-btn--ghost" disabled={busy}
                onClick={() => act(d.paused ? "resume_desk" : "pause_desk", { desk: d.desk_id })}>
                {d.paused ? "Resume" : "Pause"}
              </button>
              <button className="cml-btn cml-btn--ghost" disabled={busy}
                onClick={() => act("run_desk", { desk: d.desk_id })}>Run now</button>
            </div>
          </div>
        ))}
      </div>

      {/* The Opportunity Board — where to put the money (governed proposals you approve) */}
      <h3 className="k-subhead" style={{ marginTop: 18 }}>Opportunity Board</h3>
      <p className="cml-card__hint" style={{ marginBottom: 10 }}>
        Ranked, reasoned proposals. <strong>Sharia first</strong>, then the edge. “No edge → DCA” is a
        success state. Approving records intent — the brain still runs the full gate before any fill.
      </p>
      {board.length === 0 ? (
        <p className="k-empty">No proposals yet (needs price + macro data — add the free Alpaca + FRED keys).</p>
      ) : (
        <table className="k-table">
          <thead><tr><th>Symbol</th><th>Action</th><th>Score</th><th>Sharia</th><th>Edge</th><th>Why</th><th></th></tr></thead>
          <tbody>
            {board.map((p) => (
              <tr key={p.id}>
                <td className="cml-tick">{p.symbol}</td>
                <td><span className={`cml-badge cml-badge--${p.action === "buy" ? "green" : p.action === "avoid" ? "red" : "neutral"}`}>{p.action}</span></td>
                <td className="k-fig">{p.score ?? "—"}</td>
                <td><span className={`cml-badge cml-badge--${p.sharia_status === "compliant" || p.sharia_status === "pass" ? "green" : "red"}`}>{p.sharia_status}</span></td>
                <td><span className={`cml-verdict cml-verdict--${p.edge_allowed ? "ok" : "no"}`}>{p.edge_allowed ? "● EDGE" : "○ none"}</span></td>
                <td className="k-mono-sm" title={p.reason_chain.join(" · ")}>{p.recommended_action}</td>
                <td className="k-board__ctl">
                  <button className="cml-btn cml-btn--ghost" disabled={busy || p.action !== "buy"}
                    onClick={() => act("approve_proposal", { id: p.id })}>Approve</button>
                  <button className="cml-btn cml-btn--ghost" disabled={busy}
                    onClick={() => act("veto_proposal", { id: p.id })}>Veto</button>
                  <button className="cml-btn cml-btn--ghost" disabled={busy}
                    onClick={() => act("prioritize_proposal", { id: p.id, rank: (p.score ?? 0) + 100 })}>Pin</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p className="cml-note" style={{ marginTop: 10 }}>
        Controls are queued for the brain, which validates each as founder-only and applies the full
        Constitution + Edge Proof + approval gate. Nothing here runs in the browser or moves real money.
      </p>
    </div>
  );
}

"use client";
import { useState } from "react";

// Phase-2 interactive controls. These never run anything in the browser — they QUEUE a command into
// Supabase that the Python brain executes on its next poll (ops/command_poller.py). Paper only, and a
// live trade still needs the brain-side approval + Constitution + Edge Proof. This is a request, not an act.
export default function ControlBar({ phase, email }: { phase: number; email: string | null }) {
  const [ref, setRef] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function send(type: string, payload: Record<string, unknown> = {}) {
    setBusy(true); setMsg(null);
    try {
      const res = await fetch("/api/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, payload }),
      });
      const json = await res.json();
      setMsg(res.ok ? { ok: true, text: `Queued: ${type}${ref ? " " + ref : ""}` } : { ok: false, text: json.error || "failed" });
    } catch (e) {
      setMsg({ ok: false, text: String(e) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="cml-controls">
        <button className="cml-btn" disabled={busy} onClick={() => send("run_tick")}>
          Run paper tick
        </button>
        <input
          className="cml-input"
          placeholder="approval ref / symbol"
          value={ref}
          onChange={(e) => setRef(e.target.value)}
        />
        <button className="cml-btn cml-btn--ghost" disabled={busy || !ref} onClick={() => send("approve", { ref })}>
          Approve
        </button>
        <button className="cml-btn cml-btn--ghost" disabled={busy || !ref} onClick={() => send("veto", { ref })}>
          Veto
        </button>
      </div>
      {msg && <p className={`cml-note ${msg.ok ? "cml-ok" : "cml-err"}`}>{msg.text}</p>}
      <p className="cml-note">
        Commands are queued for the brain (phase {phase}). The brain still applies the full
        Constitution + Edge Proof + approval gate before anything happens. Nothing here moves real money.
      </p>
    </div>
  );
}

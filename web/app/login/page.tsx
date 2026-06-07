"use client";
import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

// Friends-only sign-in via Supabase magic link (email OTP). You control who can sign in from the
// Supabase dashboard (Auth -> Providers / invite users); the email allowlist gates again at the page.
export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function signIn(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr(null);
    const supabase = createClient();
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    });
    setBusy(false);
    if (error) setErr(error.message);
    else setSent(true);
  }

  return (
    <div className="k-login">
      <div className="k-seal" style={{ marginBottom: 14 }}>C</div>
      <h1>The Camel</h1>
      <p>Private operator window · paper only. Sign in with your email to view the system.</p>
      {sent ? (
        <p className="cml-ok" style={{ fontFamily: "var(--font-sans)" }}>
          Check your inbox — we sent a one-tap sign-in link to <b>{email}</b>.
        </p>
      ) : (
        <form onSubmit={signIn}>
          <input
            className="cml-input"
            style={{ width: "100%", marginBottom: 12 }}
            type="email"
            required
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button className="cml-btn" style={{ width: "100%" }} disabled={busy} type="submit">
            {busy ? "Sending…" : "Send sign-in link"}
          </button>
          {err && <p className="cml-err cml-note">{err}</p>}
        </form>
      )}
    </div>
  );
}

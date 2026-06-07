import { NextResponse, type NextRequest } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { isAllowed } from "@/lib/data";

const ALLOWED_TYPES = new Set(["run_tick", "approve", "veto"]);

// Enqueue a command for the brain. Authenticated + allowlisted only. The web NEVER executes anything —
// it inserts a 'pending' row into `commands`; ops/command_poller.py on the brain side picks it up and runs
// it through the full Constitution + Edge Proof + approval gate. Paper only.
export async function POST(request: NextRequest) {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user || !isAllowed(user.email)) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  let body: { type?: string; payload?: Record<string, unknown> };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "bad json" }, { status: 400 });
  }
  const type = String(body.type || "");
  if (!ALLOWED_TYPES.has(type)) {
    return NextResponse.json({ error: "unknown command" }, { status: 400 });
  }

  const { error } = await supabase.from("commands").insert({
    type,
    payload: body.payload ?? {},
    status: "pending",
    requested_by: user.email,
  });
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}

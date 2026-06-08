import { createClient } from "@/lib/supabase/server";
import type { Snapshot, EquityPoint } from "@/lib/types";

// Read the single latest system-state snapshot the Python brain published. RLS restricts this to
// authenticated users, so an unauthenticated request returns nothing.
export async function getLatestSnapshot(): Promise<{ snapshot: Snapshot | null; updatedAt: string | null }> {
  const supabase = createClient();
  const { data, error } = await supabase
    .from("system_state")
    .select("state, updated_at")
    .order("updated_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error || !data) return { snapshot: null, updatedAt: null };
  return { snapshot: data.state as Snapshot, updatedAt: data.updated_at as string };
}

// The paper equity track record (oldest -> newest) for the equity-curve chart.
export async function getEquityPoints(limit = 240): Promise<EquityPoint[]> {
  const supabase = createClient();
  const { data, error } = await supabase
    .from("equity_points")
    .select("ts, total_value, cash, positions_value")
    .order("ts", { ascending: false })
    .limit(limit);
  if (error || !data) return [];
  return (data as EquityPoint[]).slice().reverse(); // chronological for the chart
}

// Email allowlist (friends-only). Empty list => any authenticated user is allowed.
export function isAllowed(email: string | null | undefined): boolean {
  const raw = process.env.NEXT_PUBLIC_ALLOWED_EMAILS || "";
  const list = raw.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean);
  if (list.length === 0) return true;
  return !!email && list.includes(email.toLowerCase());
}

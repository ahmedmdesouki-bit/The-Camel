"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

// Keeps the read-only dashboard fresh: subscribes to Supabase Realtime on system_state (instant updates
// when the brain republishes) AND polls every 30s as a fallback (in case Realtime isn't enabled on the
// table). Both just call router.refresh() to re-run the server component with the latest data.
export default function LiveRefresh() {
  const router = useRouter();
  useEffect(() => {
    const supabase = createClient();
    const channel = supabase
      .channel("system_state_changes")
      .on("postgres_changes", { event: "*", schema: "public", table: "system_state" }, () => router.refresh())
      .subscribe();

    const poll = setInterval(() => router.refresh(), 30_000);
    return () => {
      clearInterval(poll);
      supabase.removeChannel(channel);
    };
  }, [router]);
  return null;
}

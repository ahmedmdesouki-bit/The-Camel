"use client";
import { createBrowserClient } from "@supabase/ssr";

// Browser Supabase client (anon key only). Used for sign-in/out and client-side command POSTs.
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}

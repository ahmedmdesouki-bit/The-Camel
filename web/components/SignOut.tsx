"use client";
import { createClient } from "@/lib/supabase/client";

export default function SignOut() {
  async function out() {
    const supabase = createClient();
    await supabase.auth.signOut();
    window.location.href = "/login";
  }
  return <button className="k-signout" onClick={out}>Sign out</button>;
}

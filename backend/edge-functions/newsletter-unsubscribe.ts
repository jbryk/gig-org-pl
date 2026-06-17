// ============================================================
// GIG — Edge Function: newsletter-unsubscribe
// Wypisuje z newslettera (status -> 'unsubscribed') i przekierowuje (302)
// na statyczną stronę potwierdzenia.  Verify JWT = OFF.
//
// Sekrety:
//   SUPABASE_URL                = (auto)
//   SUPABASE_SERVICE_ROLE_KEY   = service_role (do UPDATE w bazie)
//   SITE_URL                    = https://gig.org.pl
// ============================================================

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const SITE_URL = Deno.env.get("SITE_URL") ?? "https://gig.org.pl";

Deno.serve(async (req) => {
  const url = new URL(req.url);
  const id = url.searchParams.get("id");
  let status = "error";
  if (id) {
    try {
      const db = createClient(SUPABASE_URL, SERVICE_KEY);
      const { error } = await db.from("submissions_newsletter")
        .update({ status: "unsubscribed" }).eq("id", id);
      status = error ? "error" : "ok";
    } catch (_) { status = "error"; }
  }
  return Response.redirect(`${SITE_URL}/newsletter-wypisano.html?status=${status}`, 302);
});

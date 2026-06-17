// ============================================================
// GIG — Edge Function: send-confirmation
// Wysyła potwierdzenie do klienta po zapisie (newsletter / kontakt).
// Wyzwalane przez Database Webhook (INSERT na submissions_*).
//
// Sekrety (Supabase → Edge Functions → Secrets):
//   RESEND_API_KEY = re_xxxxxxxx
//   FROM_EMAIL     = Geodezyjna Izba Gospodarcza <biuro@gig.org.pl>  (domena zweryfikowana w Resend)
// ============================================================

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY")!;
const FROM_EMAIL = Deno.env.get("FROM_EMAIL") ?? "Geodezyjna Izba Gospodarcza <biuro@gig.org.pl>";
const FUNCTIONS_BASE = (Deno.env.get("SUPABASE_URL") ?? "") + "/functions/v1";

const C = { dark: "#16314a", mid: "#2f6f9f", light: "#cfe0ee", bg: "#eef4f9" };

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function layout(title: string, body: string): string {
  return `<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#eef0f3;font-family:'Segoe UI',Arial,sans-serif;color:#16314a;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:32px 16px;"><tr><td align="center">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 6px 24px rgba(22,49,74,.10);">
      <tr><td style="background:${C.dark};padding:24px 32px;color:#fff;">
        <table role="presentation" cellpadding="0" cellspacing="0"><tr>
          <td style="background:${C.mid};width:46px;height:46px;border-radius:8px;text-align:center;vertical-align:middle;color:#fff;font-weight:800;font-size:15px;">GIG</td>
          <td style="padding-left:12px;font-weight:700;font-size:15px;">Geodezyjna Izba Gospodarcza<br><span style="font-weight:400;font-size:12px;color:rgba(255,255,255,.6);">gig.org.pl</span></td>
        </tr></table>
      </td></tr>
      <tr><td style="height:3px;background:${C.mid};"></td></tr>
      <tr><td style="padding:32px;">
        <h1 style="margin:0 0 16px;font-size:20px;color:${C.dark};">${title}</h1>
        ${body}
      </td></tr>
      <tr><td style="background:#f6f8fa;padding:20px 32px;border-top:1px solid #e6ebf0;">
        <p style="margin:0;font-size:12px;color:#6b7c8c;line-height:1.6;">
          <strong style="color:${C.dark};">Geodezyjna Izba Gospodarcza</strong><br>
          ul. Czackiego 3/5, 00-043 Warszawa &middot; tel. 22 827 38 43<br>
          <a href="mailto:biuro@gig.org.pl" style="color:${C.mid};text-decoration:none;">biuro@gig.org.pl</a> &middot;
          <a href="https://gig.org.pl" style="color:${C.mid};text-decoration:none;">gig.org.pl</a>
        </p>
      </td></tr>
    </table>
  </td></tr></table>
</body></html>`;
}

function newsletterMail(rec: Record<string, unknown>) {
  const unsub = `${FUNCTIONS_BASE}/newsletter-unsubscribe?id=${rec.id ?? ""}`;
  const body = `
    <p style="margin:0 0 14px;font-size:15px;line-height:1.65;">Dziękujemy za zapisanie się do newslettera <strong>Geodezyjnej Izby Gospodarczej</strong>.</p>
    <p style="margin:0 0 14px;font-size:15px;line-height:1.65;">Będziesz otrzymywać informacje o aktualnościach, szkoleniach i biuletynach GIG.</p>
    <p style="margin:22px 0 0;padding-top:14px;border-top:1px solid #e6ebf0;font-size:12px;color:#90a4b4;">
      Nie chcesz otrzymywać newslettera? <a href="${unsub}" style="color:#90a4b4;text-decoration:underline;">Wypisz się jednym kliknięciem</a>.
    </p>`;
  return { subject: "Potwierdzenie zapisu do newslettera GIG", html: layout("Zapis potwierdzony ✓", body) };
}

function kontaktMail(rec: Record<string, unknown>) {
  const name = (rec.name as string) || "";
  const greet = name && name !== "Anonim" ? `Szanowny/a ${esc(name)},` : "Dzień dobry,";
  const msg = (rec.message as string) || "";
  const body = `
    <p style="margin:0 0 14px;font-size:15px;line-height:1.65;">${greet}</p>
    <p style="margin:0 0 14px;font-size:15px;line-height:1.65;">dziękujemy za kontakt z Geodezyjną Izbą Gospodarczą. Odpowiemy najszybciej, jak to możliwe.</p>
    ${msg ? `<div style="margin:0 0 16px;padding:14px 18px;background:${C.bg};border-left:4px solid ${C.mid};border-radius:6px;">
      <p style="margin:0 0 6px;font-size:12px;font-weight:700;color:${C.mid};text-transform:uppercase;">Twoja wiadomość:</p>
      <p style="margin:0;font-size:14px;line-height:1.6;white-space:pre-wrap;">${esc(msg)}</p></div>` : ""}`;
  return { subject: "Otrzymaliśmy Twoją wiadomość — GIG", html: layout("Wiadomość przyjęta ✓", body) };
}

Deno.serve(async (req) => {
  try {
    const payload = await req.json();
    const table = payload.table as string;
    const rec = (payload.record ?? {}) as Record<string, unknown>;
    const to = (rec.email as string) || "";
    if (!to) return new Response(JSON.stringify({ skipped: "brak email" }), { status: 200 });

    let mail: { subject: string; html: string } | null = null;
    if (table === "submissions_newsletter") mail = newsletterMail(rec);
    else if (table === "submissions_kontakt") mail = kontaktMail(rec);
    else return new Response(JSON.stringify({ skipped: `tabela ${table}` }), { status: 200 });

    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { "Authorization": `Bearer ${RESEND_API_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({ from: FROM_EMAIL, to: [to], subject: mail.subject, html: mail.html }),
    });
    const result = await res.json();
    if (!res.ok) { console.error("Resend:", result); return new Response(JSON.stringify({ error: result }), { status: 500 }); }
    return new Response(JSON.stringify({ ok: true, id: result.id }), { status: 200, headers: { "Content-Type": "application/json" } });
  } catch (err) {
    console.error(err);
    return new Response(JSON.stringify({ error: String(err) }), { status: 500 });
  }
});

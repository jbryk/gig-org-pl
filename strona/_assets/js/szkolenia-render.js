/* =====================================================================
   GIG — kalendarz szkoleń (publiczny render z Supabase)
   Wstawia sekcję „Kalendarz szkoleń" na stronie /szkolenia/:
   karty najbliższych szkoleń + archiwum. Dane z tabeli `szkolenia`
   (RLS: publiczny odczyt opublikowanych). Przycisk „Zapisz się” prowadzi
   do formularza kontaktowego z wpisanym tematem.
   ===================================================================== */
(function () {
  "use strict";
  if (!/\/szkolenia(\/|$)/.test(location.pathname)) return;

  var SUPABASE_URL  = "https://zlepwzeyjwpmhyxfnime.supabase.co";
  var SUPABASE_ANON = "sb_publishable_1KPF4mdln3C-cZHMIqAOFw_ZM8Go2Ji";
  var RED = "#cc0a2b";

  var css =
    ".gig-szk{max-width:1100px;margin:0 auto;padding:46px 22px;font-family:inherit;}" +
    ".gig-szk h2{font-size:30px;color:#16202a;margin:0 0 6px;text-align:center;}" +
    ".gig-szk .lead{text-align:center;color:#5b6b78;margin:0 auto 30px;max-width:60ch;}" +
    ".gig-szk-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px;}" +
    ".gig-szk-card{display:flex;gap:16px;background:#fff;border:1px solid #e7ebef;border-radius:14px;padding:20px;box-shadow:0 6px 22px rgba(20,40,60,.06);transition:transform .18s,box-shadow .18s;}" +
    ".gig-szk-card:hover{transform:translateY(-3px);box-shadow:0 12px 30px rgba(20,40,60,.12);}" +
    ".gig-szk-date{flex:0 0 64px;height:72px;border-radius:10px;background:" + RED + ";color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1;}" +
    ".gig-szk-date .d{font-size:24px;font-weight:800;}" +
    ".gig-szk-date .m{font-size:11px;text-transform:uppercase;letter-spacing:.5px;margin-top:3px;}" +
    ".gig-szk-body{flex:1;min-width:0;}" +
    ".gig-szk-body h3{font-size:17px;color:#16202a;margin:0 0 6px;line-height:1.3;}" +
    ".gig-szk-meta{font-size:13px;color:#7a8794;margin:0 0 8px;}" +
    ".gig-szk-desc{font-size:14px;color:#46535f;margin:0 0 14px;line-height:1.55;}" +
    ".gig-szk-btn{display:inline-block;background:" + RED + ";color:#fff;text-decoration:none;font-weight:700;font-size:13px;padding:9px 18px;border-radius:8px;}" +
    ".gig-szk-btn:hover{filter:brightness(.92);color:#fff;}" +
    ".gig-szk-empty{text-align:center;color:#7a8794;background:#f5f7f9;border:1px dashed #d6dde3;border-radius:12px;padding:30px;}" +
    ".gig-szk-arch{margin-top:34px;}" +
    ".gig-szk-arch summary{cursor:pointer;font-weight:700;color:#16202a;font-size:16px;padding:10px 0;}" +
    ".gig-szk-arch .gig-szk-card{opacity:.78;}" +
    ".gig-szk-loading{text-align:center;color:#7a8794;padding:20px;}";
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  var MIES = ["sty","lut","mar","kwi","maj","cze","lip","sie","wrz","paź","lis","gru"];
  function dayBadge(iso) {
    if (!iso) return '<div class="gig-szk-date"><span class="d">?</span></div>';
    var d = new Date(iso + "T00:00:00");
    return '<div class="gig-szk-date"><span class="d">' + d.getDate() + '</span><span class="m">' + MIES[d.getMonth()] + " " + d.getFullYear() + "</span></div>";
  }
  function dayHuman(iso) {
    if (!iso) return "";
    var d = new Date(iso + "T00:00:00");
    return d.toLocaleDateString("pl-PL", { day: "2-digit", month: "long", year: "numeric" });
  }
  function esc(s) { return (s == null ? "" : String(s)).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

  function card(r) {
    var place = r.is_online ? "Online" : (r.location || "");
    var when = dayHuman(r.date_start) + (r.date_end && r.date_end !== r.date_start ? " – " + dayHuman(r.date_end) : "");
    var meta = [when, place].filter(Boolean).join(" · ");
    var link = "/kontakt/?szkolenie=" + encodeURIComponent(r.title);
    var desc = r.description ? '<p class="gig-szk-desc">' + esc(r.description).slice(0, 220) + (r.description.length > 220 ? "…" : "") + "</p>" : "";
    return '<article class="gig-szk-card">' + dayBadge(r.date_start) +
      '<div class="gig-szk-body"><h3>' + esc(r.title) + "</h3>" +
      (meta ? '<p class="gig-szk-meta">' + esc(meta) + "</p>" : "") + desc +
      '<a class="gig-szk-btn" href="' + link + '">Zapisz się →</a></div></article>';
  }

  function buildSection() {
    var sec = document.createElement("section");
    sec.className = "gig-szk";
    sec.innerHTML =
      "<h2>Kalendarz szkoleń</h2>" +
      '<p class="lead">Najbliższe szkolenia organizowane przez Geodezyjną Izbę Gospodarczą. Kliknij „Zapisz się”, aby zgłosić udział.</p>' +
      '<div class="gig-szk-loading" id="gigSzkLoading">Ładowanie szkoleń…</div>' +
      '<div class="gig-szk-grid" id="gigSzkUpcoming" style="display:none"></div>' +
      '<div id="gigSzkArchWrap"></div>';
    var anchor = document.querySelector("footer, .elementor-location-footer, #colophon");
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(sec, anchor);
    else document.body.appendChild(sec);
    return sec;
  }

  function loadSdk() {
    return new Promise(function (res, rej) {
      if (window.supabase) return res();
      var s = document.createElement("script");
      s.src = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.js";
      s.onload = res; s.onerror = rej; document.head.appendChild(s);
    });
  }

  async function init() {
    buildSection();
    try {
      await loadSdk();
      var db = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON);
      var res = await db.from("szkolenia").select("*").eq("status", "published").order("date_start", { ascending: true });
      if (res.error) throw res.error;
      var rows = res.data || [];
      var today = new Date(); today.setHours(0, 0, 0, 0);
      var upcoming = [], past = [];
      rows.forEach(function (r) {
        var ref = r.date_end || r.date_start;
        if (ref && new Date(ref + "T00:00:00") < today) past.push(r); else upcoming.push(r);
      });
      past.reverse();

      document.getElementById("gigSzkLoading").style.display = "none";
      var up = document.getElementById("gigSzkUpcoming");
      if (upcoming.length) { up.innerHTML = upcoming.map(card).join(""); up.style.display = ""; }
      else { up.style.display = "none";
        up.insertAdjacentHTML("beforebegin", '<div class="gig-szk-empty">Obecnie nie ma zaplanowanych szkoleń. Zapraszamy wkrótce — lub <a href="/kontakt/">napisz do nas</a>, by otrzymać informację o najbliższych terminach.</div>'); }

      if (past.length) {
        document.getElementById("gigSzkArchWrap").innerHTML =
          '<details class="gig-szk-arch"><summary>Archiwum szkoleń (' + past.length + ")</summary>" +
          '<div class="gig-szk-grid" style="margin-top:16px">' + past.map(card).join("") + "</div></details>";
      }
    } catch (e) {
      console.error(e);
      var l = document.getElementById("gigSzkLoading");
      if (l) l.outerHTML = '<div class="gig-szk-empty">Lista szkoleń jest właśnie aktualizowana. Zapraszamy wkrótce — lub <a href="/kontakt/">napisz do nas</a> po informacje o najbliższych terminach.</div>';
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();

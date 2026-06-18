/* =====================================================================
   GIG — elementy site-wide:
   (1) pływający widget: Facebook + LinkedIn + zapis do newslettera,
   (2) rozwijane menu „O nas" → [O nas, Członkowie] (strzałka, jak Baza wiedzy).
   Wstrzykiwane na każdej stronie.
   ===================================================================== */
(function () {
  "use strict";
  var SUPABASE_URL = "https://zlepwzeyjwpmhyxfnime.supabase.co";
  var SUPABASE_ANON = "sb_publishable_1KPF4mdln3C-cZHMIqAOFw_ZM8Go2Ji";
  var FB = "https://www.facebook.com/gigorgpl";
  var LI = "https://www.linkedin.com/company/gig-geodezyjna-izba-gospodarcza";
  var RED = "#cc0a2b";

  /* ---------- CSS ---------- */
  var css =
    /* widget */
    "#gigw{position:fixed;right:18px;bottom:18px;z-index:9998;font-family:Inter,-apple-system,'Segoe UI',Arial,sans-serif;display:flex;flex-direction:column;align-items:flex-end;gap:10px;}" +
    "#gigw .gigw-panel{display:none;flex-direction:column;gap:8px;width:280px;}" +
    "#gigw.open .gigw-panel{display:flex;}" +
    "#gigw .gigw-tab{display:flex;align-items:center;gap:12px;background:#fff;border:1px solid #e6ebef;border-radius:12px;padding:12px 14px;box-shadow:0 8px 26px rgba(20,40,60,.16);text-decoration:none;color:#16202a;transition:transform .15s;}" +
    "#gigw .gigw-tab:hover{transform:translateY(-2px);text-decoration:none;}" +
    "#gigw .gigw-ic{width:38px;height:38px;border-radius:9px;flex:none;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:15px;}" +
    "#gigw .gigw-fb .gigw-ic{background:#1877f2;}#gigw .gigw-li .gigw-ic{background:#0a66c2;}#gigw .gigw-nl .gigw-ic{background:" + RED + ";}" +
    "#gigw .gigw-tx b{display:block;font-size:14px;}#gigw .gigw-tx span{font-size:12px;color:#6b7884;}" +
    "#gigw .gigw-launch{display:flex;align-items:center;gap:8px;background:" + RED + ";color:#fff;border:0;border-radius:30px;padding:12px 18px;font-weight:700;font-size:14px;cursor:pointer;box-shadow:0 10px 30px rgba(204,10,43,.4);font-family:inherit;}" +
    "#gigw .gigw-launch:hover{filter:brightness(.95);}" +
    "#gigw .gigw-nlform{display:none;gap:8px;margin-top:8px;}#gigw .gigw-nl.exp .gigw-nlform{display:flex;flex-direction:column;}" +
    "#gigw .gigw-nlform input{padding:9px 11px;border:1px solid #d6dde3;border-radius:8px;font-size:13px;font-family:inherit;}" +
    "#gigw .gigw-nlform button{background:" + RED + ";color:#fff;border:0;border-radius:8px;padding:9px;font-weight:700;font-size:13px;cursor:pointer;font-family:inherit;}" +
    "#gigw .gigw-msg{font-size:12px;margin-top:4px;}" +
    "#gigw .gigw-nlwrap{background:#fff;border:1px solid #e6ebef;border-radius:12px;padding:12px 14px;box-shadow:0 8px 26px rgba(20,40,60,.16);}" +
    /* dropdown O nas (własny, niezależny od theme JS) */
    "li.gig-has{position:relative;}" +
    "li.gig-has > .gig-sub{display:none;position:absolute;top:100%;left:0;min-width:210px;background:#fff;border:1px solid #e6ebef;border-radius:10px;box-shadow:0 14px 40px rgba(20,40,60,.16);padding:8px 0;margin:6px 0 0;list-style:none;z-index:9999;}" +
    "li.gig-has:hover > .gig-sub, li.gig-has:focus-within > .gig-sub{display:block;}" +
    "li.gig-has > .gig-sub li{margin:0;display:block;}" +
    "li.gig-has > .gig-sub a{display:block;padding:9px 18px;color:#16202a;font-size:14px;white-space:nowrap;text-decoration:none;}" +
    "li.gig-has > .gig-sub a:hover{background:#f4f6f8;color:" + RED + ";}" +
    ".gig-caret{display:inline-block;margin-left:5px;font-size:10px;vertical-align:middle;}";
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  /* ---------- (1) WIDGET ---------- */
  function buildWidget() {
    var w = document.createElement("div"); w.id = "gigw";
    w.innerHTML =
      '<div class="gigw-panel">' +
        '<a class="gigw-tab gigw-fb" href="' + FB + '" target="_blank" rel="noopener"><span class="gigw-ic">f</span><span class="gigw-tx"><b>GIG na Facebooku</b><span>Zobacz aktualności</span></span></a>' +
        '<a class="gigw-tab gigw-li" href="' + LI + '" target="_blank" rel="noopener"><span class="gigw-ic">in</span><span class="gigw-tx"><b>GIG na LinkedIn</b><span>Zobacz profil Izby</span></span></a>' +
        '<div class="gigw-nlwrap"><div class="gigw-tab gigw-nl" style="border:0;box-shadow:none;padding:0;cursor:pointer" id="gigwNlTab"><span class="gigw-ic">✉</span><span class="gigw-tx"><b>Newsletter GIG</b><span>Kliknij i zapisz się</span></span></div>' +
          '<div class="gigw-nlform"><input type="email" id="gigwEmail" placeholder="Twój e-mail" aria-label="E-mail"><button id="gigwNlBtn">Zapisz się</button><div class="gigw-msg" id="gigwMsg"></div></div></div>' +
      '</div>' +
      '<button class="gigw-launch" id="gigwLaunch" aria-expanded="false">✦ Bądź na bieżąco</button>';
    document.body.appendChild(w);

    var launch = w.querySelector("#gigwLaunch");
    launch.addEventListener("click", function () {
      var open = w.classList.toggle("open");
      launch.setAttribute("aria-expanded", String(open));
      launch.innerHTML = open ? "✕ Zamknij" : "✦ Bądź na bieżąco";
    });
    var nlTab = w.querySelector("#gigwNlTab");
    nlTab.addEventListener("click", function () { nlTab.parentElement.classList.toggle("exp"); var e = w.querySelector("#gigwEmail"); if (e) e.focus(); });
    w.querySelector("#gigwNlBtn").addEventListener("click", subscribe);
    w.querySelector("#gigwEmail").addEventListener("keydown", function (e) { if (e.key === "Enter") subscribe(); });
  }

  var dbP = null;
  function getDb() {
    if (dbP) return dbP;
    dbP = new Promise(function (res, rej) {
      if (window.supabase) return res(window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON));
      var s = document.createElement("script");
      s.src = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.js";
      s.onload = function () { res(window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON)); };
      s.onerror = rej; document.head.appendChild(s);
    });
    return dbP;
  }
  async function subscribe() {
    var email = (document.getElementById("gigwEmail").value || "").trim();
    var msg = document.getElementById("gigwMsg");
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { msg.style.color = "#c0392b"; msg.textContent = "Podaj poprawny e-mail."; return; }
    msg.style.color = "#6b7884"; msg.textContent = "Zapisywanie…";
    try {
      var db = await getDb();
      var res = await db.from("submissions_newsletter").insert({ email: email, status: "new" });
      if (res.error && res.error.code !== "23505") throw res.error;
      msg.style.color = "#1f6b3b"; msg.textContent = "✓ Dziękujemy! Zapisano.";
      document.getElementById("gigwEmail").value = "";
    } catch (e) { console.error(e); msg.style.color = "#c0392b"; msg.textContent = "Błąd — spróbuj ponownie."; }
  }

  /* ---------- (2) MENU „O nas" → dropdown ---------- */
  function enhanceMenu() {
    var links = document.querySelectorAll('a[href$="/o-nas/"], a[href="/o-nas"], a[href$="/index.php/o-nas/"]');
    links.forEach(function (a) {
      var li = a.closest("li");
      if (!li || li.dataset.gigDd) return;
      // tylko pozycje menu (mają klasę menu-item / są w <ul>)
      if (!li.closest("ul")) return;
      li.dataset.gigDd = "1";
      li.classList.add("gig-has");
      if (!a.querySelector(".gig-caret")) { var car = document.createElement("span"); car.className = "gig-caret"; car.textContent = "▾"; a.appendChild(car); }
      var sub = document.createElement("ul");
      sub.className = "gig-sub";
      sub.innerHTML = '<li><a href="/o-nas/">O nas</a></li><li><a href="/czlonkowie/">Członkowie</a></li>';
      li.appendChild(sub);
    });
  }

  function init() { buildWidget(); enhanceMenu(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();

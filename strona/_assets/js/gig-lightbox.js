/* =====================================================================
   GIG — prosty lightbox: klik w obrazek z klasą .gig-zoom → powiększenie.
   Zamknięcie: klik w tło, przycisk ×, albo Esc. Bez zależności.
   ===================================================================== */
(function () {
  "use strict";

  var css =
    ".gig-lb{position:fixed;inset:0;background:rgba(12,18,24,.86);display:none;align-items:center;justify-content:center;z-index:99999;opacity:0;transition:opacity .2s;cursor:zoom-out;padding:24px;}" +
    ".gig-lb.open{opacity:1;}" +
    ".gig-lb img{width:auto;height:auto;max-width:min(88vw,360px);max-height:84vh;border-radius:14px;box-shadow:0 24px 70px rgba(0,0,0,.55);transform:scale(.94);transition:transform .2s;cursor:default;}" +
    ".gig-lb.open img{transform:scale(1);}" +
    ".gig-lb-x{position:absolute;top:14px;right:22px;font-size:38px;line-height:1;color:#fff;background:none;border:0;cursor:pointer;opacity:.85;}" +
    ".gig-lb-x:hover{opacity:1;}";
  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  var lb;
  function build() {
    lb = document.createElement("div");
    lb.className = "gig-lb";
    lb.innerHTML = '<button class="gig-lb-x" aria-label="Zamknij">×</button><img alt="">';
    document.body.appendChild(lb);
    lb.addEventListener("click", close);
    lb.querySelector("img").addEventListener("click", function (e) { e.stopPropagation(); });
  }
  function open(src, alt) {
    if (!lb) build();
    var im = lb.querySelector("img");
    im.src = src; im.alt = alt || "";
    lb.style.display = "flex";
    setTimeout(function () { lb.classList.add("open"); }, 10);
    document.body.style.overflow = "hidden";
  }
  function close() {
    if (!lb) return;
    lb.classList.remove("open");
    document.body.style.overflow = "";
    setTimeout(function () { lb.style.display = "none"; }, 200);
  }

  document.addEventListener("click", function (e) {
    var img = e.target && e.target.closest ? e.target.closest("img.gig-zoom") : null;
    if (img) { e.preventDefault(); open(img.currentSrc || img.src, img.alt); }
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
})();

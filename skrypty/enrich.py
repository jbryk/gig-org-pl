# -*- coding: utf-8 -*-
"""Wzbogaca 65 firm GIG o: website (z domeny e-maila lub DDG), facebook, linkedin.
Zasada: tylko PEWNE dopasowania (do marki/domeny). Brak pewności -> "brak".
Darmowe: domena e-maila + DuckDuckGo HTML (bez klucza). Wznawialny (cache JSON)."""
import json, re, os, time, urllib.parse, requests

HERE = os.path.dirname(os.path.abspath(__file__))
recs = json.load(open(os.path.join(HERE, "_czlonkowie.json"), encoding="utf-8"))
CACHE = os.path.join(HERE, "_czlonkowie_enrich.json")
done = {}
if os.path.exists(CACHE):
    for x in json.load(open(CACHE, encoding="utf-8")):
        done[x["name"]] = x

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
FREE_MAIL = {"gmail.com","wp.pl","o2.pl","interia.pl","interia.eu","onet.pl","op.pl","poczta.fm",
             "vp.pl","poczta.onet.pl","ko.onet.pl","gazeta.pl","outlook.com","hotmail.com","yahoo.com",
             "tlen.pl","go2.pl","autograf.pl","neostrada.pl","poczta.pl","wp.eu","int.pl","onet.eu"}
DIRECTORY = ["panoramafirm","cylex","firmania","geoforum","targeo","aleo.com","pkt.pl","gowork",
             "oferia","baza-firm","polskiefirmy","infoveriti","krs-online","rejestr.io","bazafirm",
             "money.pl","gratka","otomoto","wikipedia","mapa.targeo","ourfreedom","zumi.pl","yelp",
             "biznesfinder","firmy.net","nocowanie","tripadvisor","goldenline","praca.pl","olx.pl",
             "gov.pl","mojabudowa","ceneo","allegro","bizdirect","companywall","emis.com","openst",
             "ratemyarea","wykop","forsal","domofony","gowork.pl","b2b","spis-firm","firmy24"]

PL = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
def norm(s): return (s or "").translate(PL).lower()
STOP = set("sp z o oo spolka jawna komandytowa akcyjna sa s c sc uslugi uslugowe uslugowo geodezyjne "
           "geodezyjno geodezja kartograficzne kartografia przedsiebiorstwo biuro firma firmy handlowe "
           "handlowo projektowe projektowo inzynieryjne inzynieryjno pracownia zaklad kancelaria mgr inz "
           "prywatne okregowe miernicze mierniczych grupa i oraz uprawniony geodeta geodezyjnej izba "
           "spzoo ograniczona odpowiedzialnoscia lok ul os al".split())

def brand_tokens(name):
    raw = re.findall(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9\-]{2,}", name)
    caps = [t for t in raw if t.isupper() and len(t) >= 3 and norm(t) not in STOP]
    toks = []
    for t in (caps if caps else raw):
        n = norm(t).replace("-", "")
        if n and n not in STOP and not n.isdigit():
            toks.append(n)
    # uniq, najdłuższe najpierw
    seen=[];
    for t in sorted(set(toks), key=len, reverse=True):
        seen.append(t)
    return seen[:4]

def dom_core(url):
    try:
        h = urllib.parse.urlparse(url if "://" in url else "http://"+url).netloc.lower()
    except Exception:
        return ""
    h = h.split(":")[0]
    if h.startswith("www."): h = h[4:]
    parts = h.split(".")
    # usuń typowe sufiksy: .com.pl .waw.pl .pl .com .eu .net .org .co
    sufx = {"pl","com","eu","net","org","co","info","biz","waw","krakow","gda","wroc","eu"}
    while len(parts) > 1 and parts[-1] in sufx:
        parts = parts[:-1]
    return parts[-1] if parts else h

def is_dir(url):
    u = url.lower()
    return any(d in u for d in DIRECTORY)

def brand_match(url, brands, email_core):
    dc = dom_core(url)
    if not dc: return False
    if email_core and (email_core == dc or email_core in dc or dc in email_core): return True
    for b in brands:
        if len(b) >= 4 and (b in dc or dc in b): return True
        # wspólny rdzeń >=5 znaków
        if len(b) >= 5 and len(dc) >= 5 and (b[:5] == dc[:5]): return True
    return False

def ddg(q, tries=2):
    for k in range(tries):
        try:
            r = requests.post("https://html.duckduckgo.com/html/", data={"q": q}, headers=UA, timeout=20)
            if r.status_code == 200 and "result__a" in r.text:
                return re.findall(r'class="result__a"[^>]*href="([^"]+)"', r.text)
            time.sleep(4 + 3*k)
        except Exception:
            time.sleep(4 + 3*k)
    return []

def live(url):
    for u in ([url] if url.startswith("http") else ["https://"+url, "http://"+url]):
        try:
            r = requests.get(u, headers=UA, timeout=15, allow_redirects=True)
            if r.status_code < 400:
                return r.url.rstrip("/")
        except Exception:
            pass
    return None

out = []
for i, x in enumerate(recs, 1):
    name = x["name"]
    if name in done and done[name].get("_v") == 2:
        out.append(done[name]); print(f"[{i}/65] cache  {name[:42]}"); continue
    email = (x.get("email") or "").strip().lower()
    edom = email.split("@")[-1] if "@" in email else ""
    elocal = email.split("@")[0] if "@" in email else ""
    ecore = dom_core(edom) if (edom and edom not in FREE_MAIL) else ""
    brands = brand_tokens(name)
    rec = {"name": name, "website": "brak", "facebook": "brak", "linkedin": "brak", "_v": 2, "_src": ""}

    # 1) WEBSITE z domeny e-maila (firmowa poczta)
    if edom and edom not in FREE_MAIL:
        lv = live(edom)
        if lv:
            rec["website"] = lv; rec["_src"] = "email"
        time.sleep(0.5)

    # 2) WEBSITE z DDG (gdy brak z e-maila)
    if rec["website"] == "brak":
        res = ddg(f"{name} {''} geodezja")
        for u in res:
            if is_dir(u) or "facebook.com" in u or "linkedin.com" in u:
                continue
            if brand_match(u, brands, ecore):
                lv = live(u)
                if lv: rec["website"] = lv; rec["_src"] = "ddg"; break
        time.sleep(2.6)

    def slug_matches(slug):
        s = norm(slug).replace("-", "").replace(".", "")
        if len(s) < 4: return False
        for b in brands:
            if len(b) >= 4 and (b in s or s in b): return True
        if ecore and len(ecore) >= 4 and (ecore in s or s in ecore): return True
        return False

    # 3) FACEBOOK — tylko profil ze slugiem pasującym do marki
    res = ddg(f"{name} facebook")
    for u in res:
        if "facebook.com/" not in u: continue
        if any(s in u for s in ["/sharer","/login","/policy","plugins","/help","/pages/category"]): continue
        slug = u.split("facebook.com/")[-1].split("?")[0].split("/")[0]
        if slug in ("profile.php","people","pages"):  # zbyt ogólne — pomiń
            continue
        if slug_matches(slug):
            rec["facebook"] = u.split("?")[0].rstrip("/"); break
    time.sleep(2.6)

    # 4) LINKEDIN — tylko /company/<slug> pasujący do marki
    res = ddg(f"{name} linkedin")
    for u in res:
        if "linkedin.com/company/" not in u: continue
        slug = u.split("linkedin.com/company/")[-1].split("?")[0].split("/")[0]
        if slug_matches(slug):
            rec["linkedin"] = u.split("?")[0].rstrip("/"); break
    time.sleep(2.6)

    out.append(rec)
    print(f"[{i}/65] {rec['_src']:5} www={rec['website'][:40]:40} fb={'Y' if rec['facebook']!='brak' else '-'} li={'Y' if rec['linkedin']!='brak' else '-'}  {name[:30]}")
    json.dump(out, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)

json.dump(out, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
w = sum(1 for o in out if o["website"] != "brak")
fb = sum(1 for o in out if o["facebook"] != "brak")
li = sum(1 for o in out if o["linkedin"] != "brak")
print(f"\nGOTOWE: www {w}/65 | fb {fb}/65 | linkedin {li}/65")

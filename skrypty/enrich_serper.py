# -*- coding: utf-8 -*-
"""Wzbogacenie przez Serper (Google) — szybko i trafnie: www (dla firm z darmową pocztą),
Facebook, LinkedIn. Tylko PEWNE dopasowania (do marki/domeny). Output: _czlonkowie_social.json."""
import json, os, re, time, urllib.parse, requests
HERE = os.path.dirname(os.path.abspath(__file__))
recs = json.load(open(os.path.join(HERE, "_czlonkowie.json"), encoding="utf-8"))
KEY = open(r"C:\Claude-projekty\!Anthropic_api_key\serper-api.txt", encoding="utf-8-sig").read().strip()
OUT = os.path.join(HERE, "_czlonkowie_social.json")
prev = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}

FREE = {"gmail.com","wp.pl","o2.pl","interia.pl","interia.eu","onet.pl","op.pl","poczta.fm","vp.pl",
        "poczta.onet.pl","ko.onet.pl","gazeta.pl","outlook.com","hotmail.com","yahoo.com","tlen.pl","go2.pl"}
DIRECTORY = ["panoramafirm","cylex","firmania","geoforum","targeo","aleo","pkt.pl","gowork","oferia",
             "baza-firm","polskiefirmy","infoveriti","krs-online","rejestr.io","bazafirm","money.pl",
             "gratka","otomoto","wikipedia","zumi","yelp","biznesfinder","firmy.net","gov.pl","ceidg",
             "mojabudowa","ceneo","allegro","companywall","spis-firm","firmy24","oferteo","booking",
             "google.","youtube.","instagram.","twitter.","x.com","mapy.cz","openstreetmap"]
PL = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
def norm(s): return (s or "").translate(PL).lower()
STOP = set("sp z o oo spolka jawna komandytowa akcyjna sa s c sc uslugi uslugowe uslugowo geodezyjne "
           "geodezyjno geodezja kartograficzne kartografia przedsiebiorstwo biuro firma firmy handlowe "
           "handlowo projektowe projektowo inzynieryjne inzynieryjno pracownia zaklad kancelaria mgr inz "
           "prywatne okregowe miernicze mierniczych grupa i oraz uprawniony geodeta ograniczona spzoo".split())
def brands(name):
    raw = re.findall(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9\-]{2,}", name)
    caps = [t for t in raw if t.isupper() and len(t) >= 3 and norm(t) not in STOP]
    toks = []
    for t in (caps if caps else raw):
        n = norm(t).replace("-", "")
        if n and n not in STOP and not n.isdigit(): toks.append(n)
    return sorted(set(toks), key=len, reverse=True)[:4]
def dom_core(url):
    try: h = urllib.parse.urlparse(url if "://" in url else "http://"+url).netloc.lower()
    except Exception: return ""
    if h.startswith("www."): h = h[4:]
    parts = [p for p in h.split(".")]
    sufx = {"pl","com","eu","net","org","co","info","biz","waw","krakow","gda","wroc"}
    while len(parts) > 1 and parts[-1] in sufx: parts = parts[:-1]
    return parts[-1] if parts else h
def slug_match(s, bs, ecore):
    s = norm(s).replace("-", "").replace(".", "").replace("_","")
    if len(s) < 4: return False
    for b in bs:
        if len(b) >= 4 and (b in s or s in b): return True
    if ecore and len(ecore) >= 4 and (ecore in s or s in ecore): return True
    return False

def serper(q):
    try:
        r = requests.post("https://google.serper.dev/search",
            headers={"X-API-KEY": KEY, "Content-Type": "application/json"},
            data=json.dumps({"q": q, "gl": "pl", "hl": "pl", "num": 10}), timeout=25)
        return r.json()
    except Exception as e:
        print("  serper err", e); return {}
def links(res):
    out = []
    for k in ("organic", "topStories"):
        for it in (res.get(k) or []):
            if it.get("link"): out.append(it["link"])
    return out
def city(a):
    m = re.search(r"\d{2}-\d{3}\s*(.+)$", a or ""); return m.group(1).strip() if m else ""

out = dict(prev)
for i, r in enumerate(recs, 1):
    nm = r["name"]
    if nm in out and out[nm].get("_v") == 1:
        print(f"[{i}/65] cache {nm[:40]}"); continue
    em = (r.get("email") or "").lower(); edom = em.split("@")[-1] if "@" in em else ""
    ecore = dom_core(edom) if (edom and edom not in FREE) else ""
    bs = brands(nm); c = city(r.get("address",""))
    rec = {"website": "", "facebook": "", "linkedin": "", "_v": 1}

    # zapytanie ogólne — łapie www + fb + li naraz
    res = serper(f"{nm} {c} geodezja"); time.sleep(0.2)
    ls = links(res)
    # website (tylko gdy firmowej domeny nie damy z e-maila — to robi gen_enrich; tu dla darmowych poczt)
    if not ecore:
        for u in ls:
            ul = u.lower()
            if any(d in ul for d in DIRECTORY) or "facebook.com" in ul or "linkedin.com" in ul: continue
            if slug_match(dom_core(u), bs, ecore):
                rec["website"] = u.split("?")[0]; break
    # fb / li z wyników ogólnych
    for u in ls:
        ul = u.lower()
        if not rec["facebook"] and "facebook.com/" in ul:
            slug = ul.split("facebook.com/")[-1].split("?")[0].split("/")[0]
            if slug not in ("profile.php","people","pages","sharer") and slug_match(slug, bs, ecore):
                rec["facebook"] = u.split("?")[0]
        if not rec["linkedin"] and "linkedin.com/company/" in ul:
            slug = ul.split("linkedin.com/company/")[-1].split("?")[0].split("/")[0]
            if slug_match(slug, bs, ecore): rec["linkedin"] = u.split("?")[0]

    # doszukanie FB jeśli brak
    if not rec["facebook"]:
        res = serper(f"{nm} {c} facebook"); time.sleep(0.2)
        for u in links(res):
            ul = u.lower()
            if "facebook.com/" in ul:
                slug = ul.split("facebook.com/")[-1].split("?")[0].split("/")[0]
                if slug not in ("profile.php","people","pages","sharer") and slug_match(slug, bs, ecore):
                    rec["facebook"] = u.split("?")[0]; break
    # doszukanie LinkedIn jeśli brak
    if not rec["linkedin"]:
        res = serper(f"{nm} linkedin"); time.sleep(0.2)
        for u in links(res):
            ul = u.lower()
            if "linkedin.com/company/" in ul:
                slug = ul.split("linkedin.com/company/")[-1].split("?")[0].split("/")[0]
                if slug_match(slug, bs, ecore): rec["linkedin"] = u.split("?")[0]; break

    out[nm] = rec
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"[{i}/65] www={'Y' if rec['website'] else '-'} fb={'Y' if rec['facebook'] else '-'} li={'Y' if rec['linkedin'] else '-'}  {nm[:36]}")

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
w=sum(1 for v in out.values() if v['website']); fb=sum(1 for v in out.values() if v['facebook']); li=sum(1 for v in out.values() if v['linkedin'])
print(f"\nSERPER: www(extra) {w} | fb {fb} | linkedin {li} / {len(recs)}")

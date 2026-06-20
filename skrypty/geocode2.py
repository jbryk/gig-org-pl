# -*- coding: utf-8 -*-
"""Dokładne geokodowanie po adresie (Nominatim STRUCTURED -> poziom budynku).
Parsuje ulicę+nr / kod / miasto; chain zapytań; raportuje precyzję.
Output: _czlonkowie_geo.json [{name, region, lat, lng, geo: building|street|city|none}]"""
import json, re, time, os, requests
HERE = os.path.dirname(os.path.abspath(__file__))
recs = json.load(open(os.path.join(HERE, "_czlonkowie.json"), encoding="utf-8"))
H = {"User-Agent": "gig-org-pl-map/2.0 (kontakt: biuro@gig.org.pl)"}

def parse(addr):
    addr = re.sub(r"\s+", " ", addr or "").strip()
    pc = re.search(r"(\d{2}-\d{3})", addr)
    postcode = pc.group(1) if pc else ""
    before = addr[:pc.start()].strip(" ,") if pc else addr
    after = addr[pc.end():].strip(" ,") if pc else ""
    # miasto = po kodzie; wyłap ewentualny numer wiejski na końcu ("Białobrzegi 67A")
    city, tail = after, ""
    m = re.match(r"^(.*?)[\s,]+(\d+[A-Za-z]?(?:/\d+\w*)?)$", after)
    if m: city, tail = m.group(1).strip(), m.group(2)
    # ulica = ostatni segment przed kodem (odcina nazwisko / prefiks miasta)
    chunks = [c.strip() for c in before.split(",") if c.strip()]
    while len(chunks) > 1 and re.match(r"^(lok\.?|m\.?)\s*\d", chunks[-1], re.I):
        chunks.pop()  # odrzuć końcowe segmenty będące numerem lokalu
    street = chunks[-1] if chunks else ""
    # adres wiejski: segment bez cyfry + numer po mieście -> użyj "miasto numer"
    village = bool(tail) and not re.search(r"\d", street)
    s = street
    s = re.sub(r"\b(ul|al|pl|os|gen|kap|mjr|plk|ks)\b\.?\s*", "", s, flags=re.I)  # \b: nie obcina "Aleja"
    s = re.sub(r"\bnr\s*", "", s, flags=re.I)
    s = re.sub(r"\s*(lok\.?|m\.?)\s*\w+\s*$", "", s, flags=re.I)   # numer lokalu
    s = re.sub(r"/\S+\s*$", "", s)                                   # /4 mieszkanie
    street = re.sub(r"\s+", " ", s).strip()
    city = re.sub(r"\s+", " ", city).strip()
    return street, city, postcode, tail, village

def nomi(params):
    p = {"format": "json", "limit": 1, "addressdetails": 1, "countrycodes": "pl"}
    p.update(params)
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search", params=p, headers=H, timeout=25)
        d = r.json()
        return d[0] if d else None
    except Exception as e:
        print("  err", e); return None

def level(res):
    if not res: return "none"
    a = res.get("address") or {}
    rank = int(res.get("place_rank", 0))
    if a.get("house_number") or rank >= 30: return "building"
    if a.get("road") or rank >= 26: return "street"
    return "city"

out = []
for i, x in enumerate(recs, 1):
    addr = x.get("address", "") or ""
    street, city, pc, tail, village = parse(addr)
    reg = x.get("region", "") or ""
    loc = (f", {pc}" if pc else (f", {reg}" if reg else "")) + ", Polska"  # kod pocztowy/wojew. dla ujednoznacznienia
    queries = []
    if village and city:
        queries.append({"q": f"{tail} {city}{loc}"})
    if street and city:
        if pc: queries.append({"street": street, "city": city, "postalcode": pc})
        queries.append({"street": street, "city": city})
        queries.append({"q": f"{street}, {city}{loc}"})
    if city:
        queries.append({"q": f"{city}{(', ' + reg) if reg else ''}, Polska"})
    best, bestrank = None, -1
    used = "none"
    for q in queries:
        res = nomi(dict(q)); time.sleep(1.1)
        if not res: continue
        lv = level(res)
        if lv in ("building", "street"):
            best, used = res, lv; break
        rank = int(res.get("place_rank", 0))
        if rank > bestrank: best, bestrank, used = res, rank, lv
    lat = float(best["lat"]) if best else None
    lng = float(best["lon"]) if best else None
    out.append({"name": x["name"], "region": x.get("region"), "lat": lat, "lng": lng, "geo": used if best else "none"})
    print(f"[{i}/65] {used:8} {(street+' / '+city)[:34]:34} -> {lat},{lng}")

json.dump(out, open(os.path.join(HERE, "_czlonkowie_geo.json"), "w", encoding="utf-8"), ensure_ascii=False)
from collections import Counter
c = Counter(o["geo"] for o in out)
print(f"\nGEO: budynek {c['building']} | ulica {c['street']} | miasto {c['city']} | brak {c['none']}  (razem {len(out)})")

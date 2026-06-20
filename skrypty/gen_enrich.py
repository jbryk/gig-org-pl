# -*- coding: utf-8 -*-
"""Scala: _czlonkowie.json (nazwy, kolejność) + _czlonkowie_geo.json (lat/lng)
   + _czlonkowie_enrich.json (www/fb/linkedin) + DESC (opisy) ->
   1) strona/_assets/js/czlonkowie-enrich.js  (window.GIG_ENRICH dla strony)
   2) backend/supabase_czlonkowie_update.sql  (UPDATE po nazwie — Jurek uruchamia)
   NIP/REGON/KRS pozostają puste do czasu pozyskania z GUS."""
import json, os, re, math, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
recs = json.load(open(os.path.join(HERE, "_czlonkowie.json"), encoding="utf-8"))
geo  = json.load(open(os.path.join(HERE, "_czlonkowie_geo.json"), encoding="utf-8"))
enr_path = os.path.join(HERE, "_czlonkowie_enrich.json")
enr = {e["name"]: e for e in (json.load(open(enr_path, encoding="utf-8")) if os.path.exists(enr_path) else [])}
gus_path = os.path.join(HERE, "_czlonkowie_ids_gus.json")  # autorytatywne z GUS (po kluczu)
gus = json.load(open(gus_path, encoding="utf-8")) if os.path.exists(gus_path) else {}
soc_path = os.path.join(HERE, "_czlonkowie_social.json")  # Serper: www(extra)/fb/linkedin
soc = json.load(open(soc_path, encoding="utf-8")) if os.path.exists(soc_path) else {}

# Opisy profilu działalności (kolejność == _czlonkowie.json). Wszystkie to firmy geodezyjne;
# specjalizacje dopisane tylko tam, gdzie nazwa/branża jest jednoznaczna.
DESC = [
 "Biuro geodezyjne z Warszawy — pomiary sytuacyjno-wysokościowe, mapy do celów projektowych, podziały i rozgraniczenia nieruchomości oraz geodezyjna obsługa inwestycji.",
 "Usługi geodezyjne dla klientów indywidualnych i firm — tyczenia, inwentaryzacje powykonawcze, mapy do celów projektowych oraz podziały działek.",
 "Kancelaria geodezyjna z Warszawy świadcząca pełen zakres prac geodezyjno-kartograficznych dla inwestycji, nieruchomości i administracji.",
 "Firma geodezyjna z Warszawy — pomiary, mapy do celów projektowych, obsługa budów oraz opracowania na potrzeby ewidencji gruntów i budynków.",
 "Geodezyjna obsługa inwestycji budowlanych i drogowych — tyczenia, inwentaryzacje powykonawcze, mapy do celów projektowych.",
 "Prywatne biuro geodezyjne z Warszawy — pomiary sytuacyjno-wysokościowe, podziały nieruchomości, mapy do celów prawnych i projektowych.",
 "Dostawca profesjonalnego sprzętu geodezyjnego i pomiarowego (tachimetry, odbiorniki GNSS, niwelatory, skanery 3D) wraz z oprogramowaniem, szkoleniami i serwisem dla branży geodezyjnej i budowlanej.",
 "Usługi geodezyjne z Radomia — pomiary, mapy do celów projektowych, podziały i rozgraniczenia oraz obsługa geodezyjna inwestycji.",
 "Firma geodezyjna z Podkarpacia świadcząca usługi w zakresie pomiarów, map do celów projektowych i obsługi inwestycji.",
 "Przedsiębiorstwo geodezyjne realizujące duże opracowania geodezyjno-kartograficzne, modernizacje baz danych (EGIB, GESUT, BDOT500) oraz kompleksową obsługę inwestycji.",
 "Spółka geodezyjna z Rzeszowa — opracowania dla administracji geodezyjno-kartograficznej, modernizacje baz danych oraz obsługa inwestycji infrastrukturalnych.",
 "Usługi geodezyjno-kartograficzne — pomiary, mapy do celów projektowych, podziały nieruchomości oraz obsługa inwestycji.",
 "Przedsiębiorstwo usług geodezyjno-projektowych — opracowania geodezyjne, mapy do celów projektowych i obsługa procesów inwestycyjnych.",
 "Przedsiębiorstwo usług geodezyjnych i kartograficznych z Sanoka — pomiary, opracowania mapowe i obsługa geodezyjna inwestycji.",
 "Spółka geodezyjna świadcząca usługi w zakresie pomiarów, opracowań kartograficznych i obsługi inwestycji budowlanych.",
 "Przedsiębiorstwo geodezyjne (spółka komandytowa) — kompleksowe opracowania geodezyjno-kartograficzne i obsługa inwestycji.",
 "Jedno z największych w Polsce przedsiębiorstw geodezyjno-kartograficznych i inżynierskich — fotogrametria, lotniczy i naziemny skaning laserowy oraz opracowania dla administracji i infrastruktury.",
 "Grupa geodezyjna realizująca pomiary, opracowania kartograficzne, modernizacje baz danych i obsługę inwestycji.",
 "Biuro geodezyjne z Tarnowa — pomiary, mapy do celów projektowych, podziały i rozgraniczenia nieruchomości.",
 "Firma usługowo-handlowa z Krakowa świadcząca usługi geodezyjne oraz obsługę pomiarową inwestycji.",
 "Usługi geodezyjne (spółka cywilna) — pomiary sytuacyjno-wysokościowe, mapy do celów projektowych, podziały nieruchomości.",
 "Pracownia geodezyjna z Krakowa — pomiary, mapy do celów projektowych, obsługa inwestycji oraz opracowania do celów prawnych.",
 "Przedsiębiorstwo geodezyjne (spółka jawna) z Krakowa — kompleksowe usługi geodezyjno-kartograficzne i obsługa inwestycji.",
 "Usługi geodezyjno-kartograficzne — pomiary, mapy do celów projektowych, podziały i rozgraniczenia nieruchomości.",
 "Przedsiębiorstwo geodezyjne oraz twórca oprogramowania dla geodezji i administracji geodezyjno-kartograficznej; opracowania i prowadzenie zasobu.",
 "Przedsiębiorstwo geodezyjne (spółka jawna) z Katowic — kompleksowe usługi geodezyjno-kartograficzne i obsługa inwestycji.",
 "Biuro geodezyjne z Bielska-Białej — pomiary, mapy do celów projektowych, podziały nieruchomości i obsługa inwestycji.",
 "Usługi geodezyjne ze Śląska — pomiary sytuacyjno-wysokościowe, mapy do celów projektowych, obsługa budów i podziały działek.",
 "Spółka geodezyjna z Katowic świadcząca usługi pomiarowe, kartograficzne i obsługę inwestycji.",
 "Usługi geodezyjne — pomiary, mapy do celów projektowych, inwentaryzacje powykonawcze i podziały nieruchomości.",
 "Geodezja i kartografia — pomiary sytuacyjno-wysokościowe, mapy do celów projektowych, podziały i rozgraniczenia nieruchomości.",
 "Biuro geodezyjne MAPAN z Sosnowca — pomiary, mapy do celów projektowych, obsługa inwestycji i podziały nieruchomości.",
 "Pracownia geodezji inżynieryjno-przemysłowej — precyzyjne pomiary przemysłowe, obsługa obiektów i inwestycji oraz geodezja inżynieryjna.",
 "Przedsiębiorstwo usług geodezyjnych z Częstochowy — kompleksowe pomiary, opracowania kartograficzne i obsługa inwestycji.",
 "Firma geodezyjna specjalizująca się w obsłudze Rodzinnych Ogrodów Działkowych (ROD), modernizacjach baz danych EGIB/GESUT/BDOT500, detekcji uzbrojenia podziemnego oraz skaningu 3D i pomiarach z dronów.",
 "Usługi geodezyjne z Sosnowca — pomiary, mapy do celów projektowych, podziały i obsługa inwestycji.",
 "Usługi geodezyjno-miernicze — pomiary sytuacyjno-wysokościowe, mapy do celów projektowych, podziały nieruchomości.",
 "Zakład usług geodezyjnych i kartograficznych PRYZMAT z Częstochowy — pomiary, opracowania mapowe i obsługa inwestycji.",
 "Biuro geodezyjne z Opola — pomiary, mapy do celów projektowych, podziały i rozgraniczenia nieruchomości.",
 "Geodezja i fotogrametria z wykorzystaniem bezzałogowych statków powietrznych (dronów) — naloty fotogrametryczne, ortofotomapy, numeryczne modele terenu i pomiary z powietrza.",
 "Przedsiębiorstwo usług geodezyjnych i kartograficznych z Lubina — pomiary, opracowania mapowe i obsługa inwestycji.",
 "Usługi geodezyjne i doradztwo — pomiary, mapy do celów projektowych oraz obsługa procesów inwestycyjnych.",
 "Biuro geodezyjne GEOPLAN — pomiary, mapy do celów projektowych, podziały nieruchomości i obsługa inwestycji.",
 "Usługi geodezyjne — pomiary sytuacyjno-wysokościowe, mapy do celów projektowych, inwentaryzacje i podziały działek.",
 "Kancelaria geodezyjna z Piotrkowa Trybunalskiego — pomiary, mapy do celów projektowych i opracowania do celów prawnych.",
 "Pracownia geodezyjna GEODELTA ze Skierniewic — kompleksowe usługi geodezyjno-kartograficzne i obsługa inwestycji.",
 "Przedsiębiorstwo usług geodezyjnych i kartograficznych (spółka cywilna) z Łodzi — pomiary, opracowania mapowe i obsługa inwestycji.",
 "Łódzkie przedsiębiorstwo geodezyjno-informatyczne — usługi geodezyjne oraz rozwiązania informatyczne dla geodezji i administracji.",
 "Firma handlowo-usługowa GEODROM — usługi geodezyjne, pomiary i mapy do celów projektowych.",
 "Geodezja (spółka cywilna) — pomiary sytuacyjno-wysokościowe, mapy do celów projektowych, podziały i rozgraniczenia nieruchomości.",
 "Przedsiębiorstwo usługowe MARS — usługi geodezyjne, pomiary i obsługa inwestycji.",
 "Przedsiębiorstwo geodezyjne GEODETA z Konina — pomiary, mapy do celów projektowych i obsługa inwestycji.",
 "Przedsiębiorstwo usług geodezyjno-kartograficznych MIERNIK — pomiary, opracowania mapowe i podziały nieruchomości.",
 "Usługi geodezyjno-kartograficzne z Szamotuł — pomiary, mapy do celów projektowych, podziały i rozgraniczenia nieruchomości.",
 "Geodeta uprawniony — pomiary sytuacyjno-wysokościowe, mapy do celów projektowych, podziały i rozgraniczenia nieruchomości.",
 "Okręgowe przedsiębiorstwo geodezyjno-kartograficzne GEOMAP — kompleksowe opracowania geodezyjne, modernizacje baz danych i obsługa inwestycji.",
 "Biuro geodezyjne PROGEO z Olsztyna — pomiary, mapy do celów projektowych, podziały nieruchomości i obsługa inwestycji.",
 "Firma usługowo-handlowa DIAZ z Gdańska — usługi geodezyjne, pomiary i obsługa inwestycji.",
 "Kancelaria geodezyjna z Gdańska — pomiary, mapy do celów projektowych i opracowania do celów prawnych.",
 "Usługi geodezyjne GEO-FINGER ze Szczecina — pomiary, mapy do celów projektowych i podziały nieruchomości.",
 "Geodezja i kartografia GEO-KOMPLEKS ze Szczecina — kompleksowe pomiary, opracowania mapowe i obsługa inwestycji.",
 "Biuro geodezyjne z Gryfina — pomiary sytuacyjno-wysokościowe, mapy do celów projektowych, podziały nieruchomości.",
 "Biuro geodezyjne GEOSYSTEM ze Szczecinka — pomiary, mapy do celów projektowych i obsługa inwestycji.",
 "Spółka geodezyjna GEOTOTAL PRO ze Szczecina — pomiary, opracowania kartograficzne i obsługa inwestycji.",
 "Przedsiębiorstwo usług geodezyjnych i kartograficznych (PUGiK) z Choszczna — pomiary, mapy do celów projektowych i obsługa inwestycji.",
]
assert len(DESC) == len(recs), f"DESC ma {len(DESC)} pozycji, firm jest {len(recs)}"

FREE_MAIL = {"gmail.com","wp.pl","o2.pl","interia.pl","interia.eu","onet.pl","op.pl","poczta.fm",
             "vp.pl","poczta.onet.pl","ko.onet.pl","gazeta.pl","outlook.com","hotmail.com","yahoo.com",
             "tlen.pl","go2.pl","autograf.pl","neostrada.pl","poczta.pl","wp.eu","int.pl","onet.eu"}
def email_site(rec):
    em = (rec.get("email") or "").strip().lower()
    if "@" in em:
        dom = em.split("@")[-1]
        if dom and dom not in FREE_MAIL and "." in dom:
            return "https://" + dom
    return ""

def origin(url):
    if not url or url == "brak": return ""
    try:
        p = urllib.parse.urlparse(url if "://" in url else "http://"+url)
        return (p.scheme or "https") + "://" + p.netloc
    except Exception:
        return url

def clean(v):
    return "" if (not v or str(v).strip().lower() == "brak") else str(v).strip()

# jitter: firmy o identycznych współrzędnych (środek miasta) rozsuwamy po okręgu (~160 m),
# żeby każda pinezka była osobno klikalna po przybliżeniu.
groups = {}
for i, g in enumerate(geo):
    if g.get("lat") is None: continue
    groups.setdefault((round(g["lat"], 4), round(g["lng"], 4)), []).append(i)
adj = {}
for (lat0, lng0), idxs in groups.items():
    if len(idxs) == 1:
        adj[idxs[0]] = (geo[idxs[0]]["lat"], geo[idxs[0]]["lng"]); continue
    R = 0.0016  # ~ 160 m
    for k, i in enumerate(idxs):
        ang = 2 * math.pi * k / len(idxs)
        dlat = R * math.cos(ang)
        dlng = R * math.sin(ang) / max(0.2, math.cos(math.radians(lat0)))
        adj[i] = (round(lat0 + dlat, 6), round(lng0 + dlng, 6))

out = {}
for i, r in enumerate(recs):
    nm = r["name"]
    e = enr.get(nm, {})
    lat, lng = adj.get(i, (geo[i].get("lat"), geo[i].get("lng")))
    s = soc.get(nm, {})
    web = origin(email_site(r)) or origin(clean(s.get("website"))) or origin(clean(e.get("website")))
    gv = gus.get(nm, {})
    out[nm] = {
        "website": web,
        "facebook": clean(s.get("facebook")) or clean(e.get("facebook")),
        "linkedin": clean(s.get("linkedin")) or clean(e.get("linkedin")),
        "description": DESC[i],
        "lat": lat, "lng": lng,
        "nip": gv.get("nip") if gv.get("gus") else None,
        "regon": gv.get("regon") if gv.get("gus") else None,
        "krs": gv.get("krs") if gv.get("gus") else None,
    }

# 1) JS dla strony
js = "window.GIG_ENRICH=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n"
jsp = os.path.join(ROOT, "strona", "_assets", "js", "czlonkowie-enrich.js")
open(jsp, "w", encoding="utf-8").write(js)

# 2) UPDATE SQL (po nazwie). Pojedyncze apostrofy podwajamy.
def q(v):
    if v is None or v == "":
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"
def qf(v):
    return "NULL" if v is None else repr(float(v))
lines = ["-- Wgranie danych wzbogaconych do tabeli czlonkowie (dopasowanie po nazwie).",
         "-- Uruchom PO supabase_czlonkowie_enrich.sql. NIP/REGON/KRS dochodzą osobno (z GUS).",
         "begin;"]
for nm, d in out.items():
    sets = [f"website={q(d['website'] or None)}",
            f"facebook={q(d['facebook'] or None)}",
            f"linkedin={q(d['linkedin'] or None)}",
            f"description={q(d['description'])}",
            f"lat={qf(d['lat'])}", f"lng={qf(d['lng'])}"]
    # NIP/REGON/KRS dopisujemy tylko gdy potwierdzone w GUS (inaczej nie nadpisujemy NULL-em)
    if d.get("nip"):   sets.append(f"nip={q(d['nip'])}")
    if d.get("regon"): sets.append(f"regon={q(d['regon'])}")
    if d.get("krs"):   sets.append(f"krs={q(d['krs'])}")
    lines.append(f"update public.czlonkowie set {', '.join(sets)} where name={q(nm)};")
lines.append("commit;")
sqlp = os.path.join(ROOT, "backend", "supabase_czlonkowie_update.sql")
open(sqlp, "w", encoding="utf-8").write("\n".join(lines) + "\n")

w = sum(1 for d in out.values() if d["website"])
fb = sum(1 for d in out.values() if d["facebook"])
li = sum(1 for d in out.values() if d["linkedin"])
gg = sum(1 for d in out.values() if d["lat"] is not None)
print(f"JS:  {jsp}  ({round(os.path.getsize(jsp)/1024,1)} KB)")
print(f"SQL: {sqlp}")
print(f"www {w}/{len(recs)} | fb {fb} | linkedin {li} | geo {gg} | opisy {len(DESC)}")

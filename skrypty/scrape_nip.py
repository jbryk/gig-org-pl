# -*- coding: utf-8 -*-
"""Zbiera KANDYDATÓW NIP/REGON/KRS ze stron WWW firm (footer/kontakt).
Walidacja sumy kontrolnej NIP -> odrzuca przypadkowe ciągi cyfr.
Dane = SAMODZIELNIE PODANE przez firmę na jej stronie; potwierdzenie autorytatywne robi gus_fetch.py.
Output: _czlonkowie_ids.json  {name: {nip, regon, krs, src}}"""
import json, os, re, time, urllib.parse, requests
HERE = os.path.dirname(os.path.abspath(__file__))
recs = json.load(open(os.path.join(HERE, "_czlonkowie.json"), encoding="utf-8"))
enr_path = os.path.join(HERE, "_czlonkowie_enrich.json")
enr = {e["name"]: e for e in (json.load(open(enr_path, encoding="utf-8")) if os.path.exists(enr_path) else [])}
soc_path = os.path.join(HERE, "_czlonkowie_social.json")
soc = json.load(open(soc_path, encoding="utf-8")) if os.path.exists(soc_path) else {}
OUT = os.path.join(HERE, "_czlonkowie_ids.json")
prev = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
FREE = {"gmail.com","wp.pl","o2.pl","interia.pl","interia.eu","onet.pl","op.pl","poczta.fm","vp.pl",
        "poczta.onet.pl","ko.onet.pl","gazeta.pl","outlook.com","hotmail.com","yahoo.com","tlen.pl","go2.pl"}

def nip_ok(d):
    if len(d) != 10 or len(set(d)) == 1: return False
    w = [6,5,7,2,3,4,5,6,7]
    return sum(int(d[i])*w[i] for i in range(9)) % 11 == int(d[9])

def site_for(rec):
    em0 = (rec.get("email") or "").lower()
    dom0 = em0.split("@")[-1] if "@" in em0 else ""
    if dom0 and dom0 not in FREE and "." in dom0:
        return "https://" + dom0  # firmowa domena e-maila = najpewniejsza
    e = enr.get(rec["name"], {}); w = e.get("website")
    if w and w != "brak": return w
    sw = soc.get(rec["name"], {}).get("website")
    if sw: return sw
    em = (rec.get("email") or "").lower()
    if "@" in em:
        dom = em.split("@")[-1]
        if dom and dom not in FREE and "." in dom: return "https://" + dom
    return ""

def fetch(url):
    try:
        r = requests.get(url, headers=UA, timeout=15, allow_redirects=True)
        if r.status_code < 400 and r.text: return r.text
    except Exception: pass
    return ""

def extract(html):
    # usuń znaczniki, zostaw tekst
    txt = re.sub(r"<[^>]+>", " ", html)
    txt = txt.replace("&nbsp;", " ")
    res = {}
    m = re.search(r"NIP[^0-9A-Za-z]{0,8}(PL)?\s*([0-9][0-9 \-]{8,14})", txt, re.I)
    if m:
        d = re.sub(r"\D", "", m.group(2))[:10]
        if nip_ok(d): res["nip"] = d
    m = re.search(r"REGON[^0-9]{0,8}([0-9][0-9 \-]{7,17})", txt, re.I)
    if m:
        d = re.sub(r"\D", "", m.group(1))
        if len(d) in (9, 14): res["regon"] = d
    m = re.search(r"KRS[^0-9]{0,8}([0-9][0-9 \-]{8,13})", txt, re.I)
    if m:
        d = re.sub(r"\D", "", m.group(1))
        if len(d) == 10: res["krs"] = d
    return res

out = dict(prev)
for i, r in enumerate(recs, 1):
    nm = r["name"]
    site = site_for(r)
    if not site:
        out.setdefault(nm, {"nip": None, "regon": None, "krs": None, "src": "brak-strony"});
        print(f"[{i}/65] —      brak strony   {nm[:38]}"); continue
    base = site.rstrip("/")
    found = {}
    for path in ["", "/kontakt", "/kontakt/", "/kontakt.html", "/contact", "/o-nas", "/o-nas/", "/firma"]:
        html = fetch(base + path)
        if html:
            found.update({k: v for k, v in extract(html).items() if k not in found})
        if "nip" in found and ("regon" in found or "krs" in found): break
        time.sleep(0.35)
    out[nm] = {"nip": found.get("nip"), "regon": found.get("regon"), "krs": found.get("krs"), "src": "www" if found else "www-brak"}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"[{i}/65] {'NIP' if found.get('nip') else '—  '}    {site_for(r)[:30]:30}  nip={found.get('nip')} regon={found.get('regon')} krs={found.get('krs')}  {nm[:24]}")

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
n = sum(1 for v in out.values() if v.get("nip"))
print(f"\nKANDYDACI NIP ze stron: {n}/65 (REGON: {sum(1 for v in out.values() if v.get('regon'))}, KRS: {sum(1 for v in out.values() if v.get('krs'))})")
print("Następnie gus_fetch.py potwierdzi je autorytatywnie (po kluczu GUS).")

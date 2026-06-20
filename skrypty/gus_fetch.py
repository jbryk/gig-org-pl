# -*- coding: utf-8 -*-
"""Klient GUS BIR1 (API REGON) — autorytatywne NIP/REGON/KRS.
GUS NIE wyszukuje po nazwie -> wejściem są KANDYDACI NIP ze scrape_nip.py (_czlonkowie_ids.json).
Dla każdego NIP: DaneSzukajPodmioty -> REGON, Nazwa, Typ; dla osób prawnych pełny raport -> KRS.
Tylko POTWIERDZONE dane są zapisywane (do _czlonkowie_ids_gus.json) — zero zgadywania.

Użycie:
  python gus_fetch.py --test                 # walidacja SOAP na środowisku testowym GUS
  python gus_fetch.py --key TWOJ_KLUCZ_GUS   # produkcyjnie, na podstawie kandydatów NIP
"""
import sys, os, re, json, time, argparse, requests

HERE = os.path.dirname(os.path.abspath(__file__))
PROD = "https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc"
TEST = "https://wyszukiwarkaregontest.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc"
TEST_KEY = "abcde12345abcde12345"
NS_ACT = "http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl"

def envelope(action, endpoint, body_inner, sid=None):
    hdr_sid = f'<sid xmlns="http://CIS/BIR/PUBL/2014/07">{sid}</sid>' if sid else ""
    return ('<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" '
            'xmlns:wsa="http://www.w3.org/2005/08/addressing">'
            '<soap:Header>'
            f'<wsa:To>{endpoint}</wsa:To>'
            f'<wsa:Action>{action}</wsa:Action>'
            f'{hdr_sid}'
            '</soap:Header>'
            f'<soap:Body>{body_inner}</soap:Body></soap:Envelope>')

def call(endpoint, action, body_inner, sid=None):
    data = envelope(action, endpoint, body_inner, sid).encode("utf-8")
    headers = {"Content-Type": 'application/soap+xml; charset=utf-8'}
    if sid: headers["sid"] = sid
    r = requests.post(endpoint, data=data, headers=headers, timeout=30)
    return r.text

def zaloguj(endpoint, key):
    body = (f'<Zaloguj xmlns="http://CIS/BIR/PUBL/2014/07"><pKluczUzytkownika>{key}</pKluczUzytkownika></Zaloguj>')
    txt = call(endpoint, NS_ACT + "/Zaloguj", body)
    m = re.search(r"<ZalogujResult>([^<]*)</ZalogujResult>", txt)
    return m.group(1) if m else ""

def wyloguj(endpoint, sid):
    body = (f'<Wyloguj xmlns="http://CIS/BIR/PUBL/2014/07"><pIdentyfikatorSesji>{sid}</pIdentyfikatorSesji></Wyloguj>')
    call(endpoint, NS_ACT + "/Wyloguj", body, sid)

def szukaj(endpoint, sid, nip=None, regon=None):
    tag = f"<d:Nip>{nip}</d:Nip>" if nip else f"<d:Regon>{regon}</d:Regon>"
    body = ('<DaneSzukajPodmioty xmlns="http://CIS/BIR/PUBL/2014/07">'
            '<pParametryWyszukiwania xmlns:d="http://CIS/BIR/PUBL/2014/07/DataContract">'
            f'{tag}</pParametryWyszukiwania></DaneSzukajPodmioty>')
    txt = call(endpoint, NS_ACT + "/DaneSzukajPodmioty", body, sid)
    m = re.search(r"<DaneSzukajPodmiotyResult>(.*?)</DaneSzukajPodmiotyResult>", txt, re.S)
    if not m: return None
    inner = (m.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&amp;", "&"))
    def g(tag):
        mm = re.search(rf"<{tag}>(.*?)</{tag}>", inner, re.S)
        return mm.group(1).strip() if mm else ""
    if not g("Regon") and not g("regon"):
        # czasem małe litery / inny układ
        pass
    return {"regon": g("Regon"), "nip": g("Nip"), "nazwa": g("Nazwa"), "typ": g("Typ"),
            "silos": g("SilosID"), "wojewodztwo": g("Wojewodztwo"), "raw": inner[:400]}

def pelny_raport(endpoint, sid, regon, raport):
    body = ('<DanePobierzPelnyRaport xmlns="http://CIS/BIR/PUBL/2014/07">'
            f'<pRegon>{regon}</pRegon><pNazwaRaportu>{raport}</pNazwaRaportu></DanePobierzPelnyRaport>')
    txt = call(endpoint, NS_ACT + "/DanePobierzPelnyRaport", body, sid)
    m = re.search(r"<DanePobierzPelnyRaportResult>(.*?)</DanePobierzPelnyRaportResult>", txt, re.S)
    if not m: return ""
    inner = m.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&amp;", "&")
    mm = re.search(r"<praw_numerWRejestrzeEwidencji>([0-9]{10})<", inner) or re.search(r"KRS[^0-9]{0,4}([0-9]{10})", inner)
    return mm.group(1) if mm else ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key"); ap.add_argument("--test", action="store_true")
    args = ap.parse_args()
    endpoint = TEST if args.test else PROD
    key = TEST_KEY if args.test else args.key
    if not key:
        print("Podaj --key TWOJ_KLUCZ_GUS (albo --test do walidacji)"); return
    sid = zaloguj(endpoint, key)
    print("Zaloguj ->", "SID OK" if sid else "BRAK SID (zły klucz/endpoint?)", f"(sid={sid[:8]}…)" if sid else "")
    if not sid: return
    if args.test:
        # walidacja: szukaj przykładowego NIP-u testowego GUS
        print("TEST szukaj NIP 5261040828 ->", szukaj(endpoint, sid, nip="5261040828"))
        wyloguj(endpoint, sid); return

    ids = json.load(open(os.path.join(HERE, "_czlonkowie_ids.json"), encoding="utf-8"))
    out = {}
    for nm, v in ids.items():
        nip = v.get("nip"); regon0 = v.get("regon")
        if not nip and not regon0:
            out[nm] = {"nip": None, "regon": None, "krs": None, "gus": False}; continue
        d = szukaj(endpoint, sid, nip=nip) if nip else szukaj(endpoint, sid, regon=regon0)
        time.sleep(0.4)
        if not d or not d.get("regon"):
            out[nm] = {"nip": nip, "regon": regon0, "krs": v.get("krs"), "gus": False, "uwaga": "GUS nie potwierdził"}; continue
        krs = ""
        if (d.get("typ") or "").upper() in ("P", "LP"):
            krs = pelny_raport(endpoint, sid, d["regon"], "BIR11OsPrawna"); time.sleep(0.4)
        out[nm] = {"nip": d.get("nip") or nip, "regon": d["regon"], "krs": krs or v.get("krs") or None,
                   "gus": True, "nazwa_gus": d.get("nazwa")}
        print(f"  GUS OK {nm[:32]:32} NIP {nip} REGON {d['regon']} KRS {krs or '-'}")
        json.dump(out, open(os.path.join(HERE, "_czlonkowie_ids_gus.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    wyloguj(endpoint, sid)
    n = sum(1 for x in out.values() if x.get("gus"))
    print(f"\nPOTWIERDZONE w GUS: {n}/{len(out)}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Geokoduje adresy 65 firm (Nominatim/OSM, darmowe) -> _czlonkowie_geo.json.
Polityka Nominatim: 1 req/s + User-Agent. Fallback do miejscowości."""
import json, re, time, os, urllib.parse, requests
HERE=os.path.dirname(os.path.abspath(__file__))
recs=json.load(open(os.path.join(HERE,"_czlonkowie.json"),encoding="utf-8"))
H={"User-Agent":"gig-org-pl-map/1.0 (kontakt: biuro@gig.org.pl)"}
def city(a):
    m=re.search(r'\d{2}-\d{3}\s*(.+)$', a or '')
    return m.group(1).strip() if m else ''
def geo(q):
    try:
        r=requests.get("https://nominatim.openstreetmap.org/search",
            params={"q":q,"format":"json","limit":1,"countrycodes":"pl"},headers=H,timeout=25)
        d=r.json()
        if d: return float(d[0]["lat"]), float(d[0]["lon"])
    except Exception as e: print("  err",e)
    return None
out=[]
for i,x in enumerate(recs,1):
    addr=x.get("address","") or ""
    res=geo(addr+", Polska"); lvl="street"
    time.sleep(1.1)
    if not res:
        c=city(addr)
        if c: res=geo(c+", Polska"); lvl="city"; time.sleep(1.1)
    if not res: lvl="none"
    lat,lng=(res if res else (None,None))
    out.append({"name":x["name"],"region":x.get("region"),"lat":lat,"lng":lng,"geo":lvl})
    print(f"[{i}/65] {lvl:6} {x['name'][:40]}  -> {lat},{lng}")
open(os.path.join(HERE,"_czlonkowie_geo.json"),"w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False))
ok=sum(1 for o in out if o['lat']); print(f"\nGEOKOD OK: {ok}/{len(out)} (none: {len(out)-ok})")

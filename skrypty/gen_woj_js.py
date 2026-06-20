# -*- coding: utf-8 -*-
"""_woj.geojson -> strona/_assets/js/woj-geojson.js (window.GIG_WOJ), zaokrąglone do 3 miejsc."""
import json, os
HERE=os.path.dirname(os.path.abspath(__file__))
d=json.load(open(os.path.join(HERE,"_woj.geojson"),encoding="utf-8"))
def r(x): return round(x,3)
def fix(c):
    if isinstance(c,list):
        if c and isinstance(c[0],(int,float)): return [r(c[0]),r(c[1])]
        return [fix(i) for i in c]
    return c
for f in d["features"]:
    f["geometry"]["coordinates"]=fix(f["geometry"]["coordinates"])
    p=f["properties"];
    # zachowaj tylko nazwę (lower) jako 'nazwa'
    nm=p.get("nazwa") or p.get("name") or ""
    f["properties"]={"nazwa":nm.lower()}
out=os.path.join(os.path.dirname(HERE),"strona","_assets","js","woj-geojson.js")
open(out,"w",encoding="utf-8").write("window.GIG_WOJ="+json.dumps(d,ensure_ascii=False,separators=(",",":"))+";\n")
print("Zapisano",out,"~",round(os.path.getsize(out)/1024,1),"KB, województw:",len(d["features"]))

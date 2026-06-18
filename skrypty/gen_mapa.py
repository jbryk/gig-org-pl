#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Z GeoJSON województw (_woj.geojson) buduje _assets/js/mapa-data.js:
   window.GIG_MAPA = {viewBox, regions:[{slug,name,d}]}.
   Projekcja prosta z korektą cos(lat), dopasowana do viewBox."""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(HERE, "_woj.geojson")
out = os.path.join(os.path.dirname(HERE), "strona", "_assets", "js", "mapa-data.js")
d = json.load(open(src, encoding="utf-8"))
feats = d["features"]

# bounding box
xs=[]; ys=[]
def coords_iter(geom):
    t=geom["type"]; c=geom["coordinates"]
    if t=="Polygon": return [c]
    if t=="MultiPolygon": return c
    return []
for f in feats:
    for poly in coords_iter(f["geometry"]):
        for ring in poly:
            for lon,lat in ring:
                xs.append(lon); ys.append(lat)
minLon,maxLon=min(xs),max(xs); minLat,maxLat=min(ys),max(ys)
meanLat=math.radians((minLat+maxLat)/2); kx=math.cos(meanLat)
H=580.0; pad=8.0
dataH=(maxLat-minLat); dataW=(maxLon-minLon)*kx
scale=(H-2*pad)/dataH
W=dataW*scale+2*pad
def px(lon,lat):
    x=pad+(lon-minLon)*kx*scale
    y=pad+(maxLat-lat)*scale
    return round(x,1),round(y,1)
def ring_d(ring):
    pts=[px(lon,lat) for lon,lat in ring]
    s="M"+f"{pts[0][0]} {pts[0][1]}"
    for x,y in pts[1:]: s+=f"L{x} {y}"
    return s+"Z"
def cap(s): return s[:1].upper()+s[1:]
regions=[]
for f in feats:
    nm=f["properties"].get("nazwa") or f["properties"].get("name")
    dpath="".join(ring_d(ring) for poly in coords_iter(f["geometry"]) for ring in poly)
    regions.append({"slug":nm.lower(),"name":cap(nm),"d":dpath})
data={"viewBox":f"0 0 {round(W,1)} {round(H,1)}","regions":regions}
os.makedirs(os.path.dirname(out),exist_ok=True)
open(out,"w",encoding="utf-8").write("window.GIG_MAPA="+json.dumps(data,ensure_ascii=False)+";\n")
print("Zapisano:",out)
print("viewBox:",data["viewBox"],"| województw:",len(regions),"| rozmiar pliku ~",round(os.path.getsize(out)/1024),"KB")
PY = None

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crawler/mirror gig.org.pl -> statyka (katalog strona/).
Poprawki: wyklucza /wp-json/, /feed/, /comments/, query-pages; dokumenty
(docx/pdf/xlsx...) traktuje jako zasoby; zbyt duze pliki zostawia jako linki
absolutne (do pozniejszej migracji). Idempotentny.
"""
import os, re, sys, time
from urllib.parse import urljoin, urlparse, urldefrag
import requests
from bs4 import BeautifulSoup

BASE = "https://gig.org.pl"
HOSTS = {"gig.org.pl", "www.gig.org.pl"}
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "strona")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; gig-mirror/1.1; static migration)"}
MAX_PAGES = 90
MAX_ASSET_BYTES = 25 * 1024 * 1024   # >25MB -> zostaw link absolutny

ASSET_EXT = {
    "css","js","mjs","png","jpg","jpeg","gif","svg","webp","avif","ico","bmp",
    "woff","woff2","ttf","eot","otf","pdf","mp4","webm","ogg","mp3","mov","json","map","txt",
    "doc","docx","xls","xlsx","ppt","pptx","zip","rar","7z","csv"
}
EXCLUDE_SUBSTR = ("/wp-json/","/feed/","/comments/","/wp-admin/","/xmlrpc",
                  "/author/","/wp-includes/","/wp-login","/trackback","/cdn-cgi/")

session = requests.Session(); session.headers.update(HEADERS)
visited_pages, saved_assets, big_skipped, errors = set(), set(), set(), []
queue = []

def log(*a): print(*a); sys.stdout.flush()
def clean_url(u): return urldefrag(u)[0]

def is_internal(u):
    try: h = urlparse(u).netloc.lower()
    except Exception: return False
    return h == "" or h in HOSTS

def path_no_query(u): return urlparse(u).path
def ext_of(path):
    seg = path.rstrip("/").split("/")[-1]
    return seg.rsplit(".",1)[-1].lower() if "." in seg else ""
def is_asset_path(path): return ext_of(path) in ASSET_EXT

def local_page_file(path):
    p = path.strip("/")
    rel = "index.html" if p == "" else os.path.join(p, "index.html")
    return os.path.join(OUT, rel.replace("/", os.sep))
def local_asset_file(path):
    p = path.lstrip("/")
    if p == "" or p.endswith("/"): p += "index"
    return os.path.join(OUT, p.replace("/", os.sep))
def ensure_dir(fp): os.makedirs(os.path.dirname(fp), exist_ok=True)

def fetch(u, binary=False):
    for attempt in (1,2):
        try:
            r = session.get(u, timeout=40, stream=binary)
            if r.status_code == 200: return r
            log(f"  ! {r.status_code} {u}"); errors.append((u, r.status_code)); return None
        except Exception as e:
            if attempt == 2: log(f"  ! err {u}: {e}"); errors.append((u, str(e))); return None
            time.sleep(1)

URL_IN_CSS = re.compile(r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""", re.I)
IMPORT_IN_CSS = re.compile(r"""@import\s+['"]([^'"]+)['"]""", re.I)

def rewrite_css(css, css_url):
    def ru(m):
        ref = m.group(1).strip()
        if ref.startswith(("data:","#")): return m.group(0)
        absu = urljoin(css_url, ref)
        if is_internal(absu): return f"url({download_asset(absu)})"
        return m.group(0)
    def ri(m):
        absu = urljoin(css_url, m.group(1).strip())
        if is_internal(absu): return f'@import "{download_asset(absu)}"'
        return m.group(0)
    return IMPORT_IN_CSS.sub(ri, URL_IN_CSS.sub(ru, css))

def download_asset(abs_url):
    """Zwraca root-rel (/path) jesli pobrano, albo absolutny URL jesli pominieto (za duzy/blad)."""
    abs_url = clean_url(abs_url)
    path = path_no_query(abs_url)
    if not path: return abs_url
    root_rel = path if path.startswith("/") else "/"+path
    if root_rel in saved_assets: return root_rel
    if abs_url in big_skipped: return abs_url
    is_css = ext_of(path) == "css"
    r = fetch(abs_url, binary=not is_css)
    if r is None: return abs_url
    fp = local_asset_file(path); ensure_dir(fp)
    if is_css:
        saved_assets.add(root_rel)
        open(fp,"w",encoding="utf-8").write(rewrite_css(r.text, abs_url))
        log(f"  css {root_rel}")
    else:
        content = r.content
        if len(content) > MAX_ASSET_BYTES:
            big_skipped.add(abs_url); log(f"  SKIP duzy ({len(content)//1024//1024}MB) {root_rel}")
            return abs_url
        saved_assets.add(root_rel)
        open(fp,"wb").write(content)
    return root_rel

def to_page_rel(abs_url):
    path = urlparse(abs_url).path or "/"
    if not path.endswith("/") and "." not in path.split("/")[-1]: path += "/"
    return path if path.startswith("/") else "/"+path

def excluded_page(path):
    low = path.lower()
    return any(s in low for s in EXCLUDE_SUBSTR) or low.rstrip("/").endswith("/feed")

def enqueue(u):
    u = clean_url(u)
    if "\\" in u or '"' in u or "'" in u: return
    p = urlparse(u)
    if p.netloc and p.netloc.lower() not in HOSTS: return
    if p.query: return
    path = p.path or "/"
    if is_asset_path(path) or excluded_page(path): return
    if "/wp-content/" in path.lower(): return
    norm = BASE + to_page_rel(u)
    if norm not in visited_pages and norm not in queue: queue.append(norm)

def handle_ref(page_url, ref):
    ref = (ref or "").strip()
    if not ref or ref.startswith(("data:","mailto:","tel:","#","javascript:")): return None
    if "\\" in ref or '"' in ref: return None
    absu = clean_url(urljoin(page_url, ref))
    if not is_internal(absu): return None
    path = path_no_query(absu)
    if is_asset_path(path):
        return download_asset(absu)
    if excluded_page(path):
        return None
    rr = to_page_rel(absu); enqueue(BASE + rr); return rr

def rewrite_srcset(page_url, value):
    out = []
    for item in value.split(","):
        item = item.strip()
        if not item: continue
        bits = item.split(); url = bits[0]; rest = " ".join(bits[1:])
        new = handle_ref(page_url, url) or url
        out.append((new + (" "+rest if rest else "")).strip())
    return ", ".join(out)

def process_page(page_url):
    r = fetch(page_url)
    if r is None: return
    ctype = r.headers.get("Content-Type","")
    if "html" not in ctype.lower():
        log(f"  (pomijam nie-HTML: {ctype}) {page_url}"); return
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup.find_all(True):
        if tag.has_attr("srcset"): tag["srcset"] = rewrite_srcset(page_url, tag["srcset"])
        if tag.has_attr("imagesrcset"): tag["imagesrcset"] = rewrite_srcset(page_url, tag["imagesrcset"])
        for attr in ("href","src","poster","data-src","data-lazy-src","data-bg"):
            if tag.has_attr(attr) and isinstance(tag.get(attr), str):
                new = handle_ref(page_url, tag[attr])
                if new: tag[attr] = new
        if tag.name == "meta" and tag.has_attr("content"):
            prop = (tag.get("property") or tag.get("name") or "").lower()
            if prop in ("og:url","og:image","twitter:image","og:image:secure_url"):
                new = handle_ref(page_url, tag["content"])
                if new: tag["content"] = new
    for tag in soup.find_all(style=True):
        tag["style"] = URL_IN_CSS.sub(
            lambda m: (lambda n: f"url({n})" if n else m.group(0))(handle_ref(page_url, m.group(1))), tag["style"])
    for tag in soup.find_all("style"):
        if tag.string: tag.string.replace_with(rewrite_css(tag.string, page_url))
    fp = local_page_file(urlparse(page_url).path or "/"); ensure_dir(fp)
    open(fp,"w",encoding="utf-8").write(str(soup))
    log(f"PAGE {urlparse(page_url).path}")

def seed_from_sitemaps():
    urls = []
    idx = fetch("https://gig.org.pl/wp-sitemap.xml")
    subs = re.findall(r"<loc>([^<]+)</loc>", idx.text) if idx else []
    for s in subs:
        if "users" in s: continue
        rr = fetch(s)
        if rr: urls += re.findall(r"<loc>([^<]+)</loc>", rr.text)
    return urls

def main():
    log(f"OUT = {OUT}")
    for s in [BASE + "/"] + seed_from_sitemaps(): enqueue(s)
    log(f"Seed: {len(queue)} stron")
    count = 0
    while queue and count < MAX_PAGES:
        u = queue.pop(0)
        if u in visited_pages: continue
        visited_pages.add(u); count += 1
        log(f"[{count}] {u}"); process_page(u); time.sleep(0.2)
    log(f"\nGOTOWE: {len(visited_pages)} stron, {len(saved_assets)} zasobow pobranych")
    if big_skipped:
        log(f"POMINIETE (za duze, linki zostaja absolutne): {len(big_skipped)}")
        for u in sorted(big_skipped): log(f"  - {u}")
    if errors:
        log(f"BLEDY/404: {len(errors)}")
        for u, c in errors[:25]: log(f"  - [{c}] {u}")

if __name__ == "__main__":
    main()

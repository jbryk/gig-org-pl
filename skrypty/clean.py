#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Czyszczenie + lokalizacja SEO zmirrorowanych stron gig.org.pl (katalog strona/).
- usuwa cruft WordPressa (RSD/xmlrpc, wlwmanifest, REST api.w.org, oEmbed, feedy,
  generator, emoji),
- ustawia canonical + og:url na absolutny https://gig.org.pl/<sciezka>/,
- wstrzykuje forms_integration.js przed </body> (idempotentnie).
Idempotentny: ponowne uruchomienie nie duplikuje wstrzyknięć.
Uruchom: python clean.py
"""
import os, glob
from bs4 import BeautifulSoup

CANON_BASE = "https://gig.org.pl"
STRONA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "strona")
FORMS_JS = "/_assets/js/forms_integration.js"

REMOVE_REL = {"EditURI", "wlwmanifest", "pingback", "https://api.w.org/", "shortlink"}
REMOVE_LINK_TYPES = {"application/json", "application/rss+xml",
                     "application/json+oembed", "text/xml+oembed", "application/atom+xml"}

def page_path(fp):
    rel = os.path.relpath(fp, STRONA).replace(os.sep, "/")
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[:-len("index.html")]
    return "/" + rel

def rel_list(tag):
    r = tag.get("rel")
    if not r:
        return []
    return r if isinstance(r, list) else [r]

def clean_file(fp):
    html = open(fp, encoding="utf-8").read()
    soup = BeautifulSoup(html, "html.parser")
    changed = 0

    # --- usun cruft <link> ---
    for link in soup.find_all("link"):
        rels = set(rel_list(link))
        typ = (link.get("type") or "").lower()
        href = (link.get("href") or "")
        if rels & REMOVE_REL or typ in REMOVE_LINK_TYPES \
           or "oembed" in href or "/xmlrpc.php" in href or "/wp-json" in href \
           or href.endswith("/feed/") or "/comments/feed" in href:
            link.decompose(); changed += 1

    # --- usun generator/meta cruft ---
    for m in soup.find_all("meta"):
        name = (m.get("name") or "").lower()
        if name == "generator":
            m.decompose(); changed += 1

    # --- usun emoji (script src + inline) ---
    for s in soup.find_all("script"):
        src = s.get("src") or ""
        txt = s.string or ""
        if "wp-emoji-release" in src or "_wpemojiSettings" in txt or "concatemoji" in txt:
            s.decompose(); changed += 1

    # --- canonical + og:url -> absolutne ---
    path = page_path(fp)
    canon = CANON_BASE + path
    can = soup.find("link", rel="canonical")
    if not can:
        can = soup.find("link", attrs={"rel": ["canonical"]})
    if can:
        can["href"] = canon
    elif soup.head:
        new = soup.new_tag("link", rel="canonical", href=canon)
        soup.head.append(new)
    ogu = soup.find("meta", attrs={"property": "og:url"})
    if ogu:
        ogu["content"] = canon

    # --- wstrzyknij forms_integration.js (raz) ---
    if not soup.find("script", attrs={"data-gig-forms": "1"}):
        tag = soup.new_tag("script", src=FORMS_JS)
        tag["defer"] = ""
        tag["data-gig-forms"] = "1"
        (soup.body or soup).append(tag)
        changed += 1

    open(fp, "w", encoding="utf-8").write(str(soup))
    return changed

def main():
    files = glob.glob(os.path.join(STRONA, "**", "index.html"), recursive=True)
    total = 0
    for fp in files:
        c = clean_file(fp)
        total += c
        print(f"  {page_path(fp):45s} zmian: {c}")
    print(f"\nGOTOWE: {len(files)} stron, lacznie {total} operacji czyszczenia/wstrzyknięcia")

if __name__ == "__main__":
    main()

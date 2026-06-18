#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wstrzykuje <script src="/_assets/js/gig-site.js"> przed </body> na wszystkich
stronach publicznych (poza /admin/). Idempotentny."""
import os, glob
STRONA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "strona")
TAG = '<script defer src="/_assets/js/gig-site.js"></script>'
n = 0
for fp in glob.glob(os.path.join(STRONA, "**", "*.html"), recursive=True):
    rel = os.path.relpath(fp, STRONA).replace(os.sep, "/")
    if rel.startswith("admin/"):
        continue
    html = open(fp, encoding="utf-8").read()
    if "gig-site.js" in html:
        continue
    if "</body>" not in html:
        continue
    idx = html.rfind("</body>")
    html = html[:idx] + TAG + "\n" + html[idx:]
    open(fp, "w", encoding="utf-8").write(html)
    n += 1
    print("  +", rel)
print(f"\nWstrzyknięto na {n} stronach.")

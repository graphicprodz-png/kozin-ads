"""Render the PDF usage guide for one or more apps from pdf_template.html using Playwright.

Usage: python3 build_guides.py [key1 key2 ...]   (default: all apps)
Requires: pip install playwright && playwright install chromium
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app_data import applications

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TPL_PATH = os.path.join(os.path.dirname(__file__), 'pdf_template.html')
HTML_OUT = os.path.join(REPO_ROOT, 'tools', '_pdf_build')
PDF_OUT = os.path.join(REPO_ROOT, 'guides')

os.makedirs(HTML_OUT, exist_ok=True)
os.makedirs(PDF_OUT, exist_ok=True)

TPL = open(TPL_PATH, encoding='utf-8').read()

keys = sys.argv[1:] or list(applications.keys())

built_html_paths = {}
for key in keys:
    a = applications[key]
    html = TPL
    html = html.replace("__ROOT__", "file://" + REPO_ROOT)
    html = html.replace("__LOGO__", a["LOGO"])
    html = html.replace("__NAME__", a["NAME"])
    html = html.replace("__VERSION__", a["VERSION"])
    html = html.replace("__TAGLINE__", a["TAGLINE"])
    html = html.replace("__FEATURES__", "\n".join(f"    <li>{f}</li>" for f in a["FEATURES"]))
    html = html.replace("__USAGE__", "\n".join(f"    <li>{u}</li>" for u in a["USAGE"]))
    out_html = os.path.join(HTML_OUT, f"{key}.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    built_html_paths[key] = out_html

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    for key, path in built_html_paths.items():
        pg = b.new_page()
        pg.goto("file://" + path)
        pg.wait_for_timeout(250)
        pg.pdf(
            path=os.path.join(PDF_OUT, f"{key}-guide.pdf"),
            format="A4",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        pg.close()
        print("built guide:", key)
    b.close()

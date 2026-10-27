"""Render the premium bilingual PDF usage guide for one or more apps from
pdf_template.html using Playwright.

Usage: python3 build_guides.py [key1 key2 ...]   (default: all apps)
Requires: pip install playwright && playwright install chromium
"""
import datetime, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from app_data import applications

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TPL_PATH = os.path.join(os.path.dirname(__file__), 'pdf_template.html')
HTML_OUT = os.path.join(REPO_ROOT, 'tools', '_pdf_build')
PDF_OUT = os.path.join(REPO_ROOT, 'guides')

os.makedirs(HTML_OUT, exist_ok=True)
os.makedirs(PDF_OUT, exist_ok=True)

TPL = open(TPL_PATH, encoding='utf-8').read()

# Same facts as the app pages (build_apps.py): confirmed from each app's own
# build.gradle / AndroidManifest.xml in kitchen-calc — identical across all 5 apps.
MIN_ANDROID = "7.0+"
PERMISSIONS = "الإنترنت"
YEAR = str(datetime.date.today().year)

def human_size(path):
    if not os.path.isfile(path):
        return "—"
    n = os.path.getsize(path)
    mb = n / (1024 * 1024)
    return f"{mb:.1f}MB" if mb >= 1 else f"{n // 1024}KB"

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
    html = html.replace("__TAGLINE_EN__", a["TAGLINE_EN"])
    html = html.replace("__AUDIENCE__", a["AUDIENCE"])
    html = html.replace("__AUDIENCE_EN__", a["AUDIENCE_EN"])
    html = html.replace("__PRIMARY__", a["COLOR"]["primary"])
    html = html.replace("__ACCENT__", a["COLOR"]["accent"])
    html = html.replace("__YEAR__", YEAR)

    hl = "\n".join(
        f'''    <div class="hl-card">
      <div class="ic">{h["icon"]}</div>
      <h3>{h["title"]}<span class="en">{h["title_en"]}</span></h3>
      <p>{h["desc"]}</p>
      <p class="en">{h["desc_en"]}</p>
    </div>'''
        for h in a["HIGHLIGHTS"]
    )
    html = html.replace("__HIGHLIGHTS__", hl)

    apk_path = os.path.join(REPO_ROOT, 'apks', a["APK"])
    facts = [
        ("📦", human_size(apk_path), "الحجم", "Size"),
        ("🤖", MIN_ANDROID, "أندرويد", "Android"),
        ("🌐", PERMISSIONS, "الأذونات", "Permissions"),
        ("🏷️", "Construtech", "المطور", "Developer"),
    ]
    facts_html = "\n".join(
        f'    <div class="fact"><b>{ic} {val}</b><span class="ar">{lbl_ar}</span><span class="en">{lbl_en}</span></div>'
        for ic, val, lbl_ar, lbl_en in facts
    )
    html = html.replace("__FACTS__", facts_html)

    if a["SHOTS"]:
        shots_root = "file://" + REPO_ROOT
        shots = "\n".join(
            f'''    <div class="shot">
      <div class="frame"><img src="{shots_root}/screenshots/{key}/{s}"></div>
      <div class="cap">لقطة من {a["NAME"]}<span class="en">App screenshot</span></div>
    </div>'''
            for s in a["SHOTS"]
        )
        shots_html = f'  <div class="shots-grid">\n{shots}\n  </div>'
    else:
        shots_html = (
            '  <div class="no-shots">'
            'ما قدرناش نجيبو لقطات شاشة حقيقية لهاذ التطبيق — محتواه مخزن بصيغة ما تتقراش مباشرة من برا.'
            '<div class="en">We couldn\'t capture real screenshots for this app — its content ships in a format that can\'t be read directly from outside.</div>'
            '</div>'
        )
    html = html.replace("__SHOTS__", shots_html)

    feat_rows = "\n".join(
        f'''    <div class="feat-row"><div class="chk">✓</div><div class="tx">{fr}<div class="en">{fe}</div></div></div>'''
        for fr, fe in zip(a["FEATURES"], a["FEATURES_EN"])
    )
    html = html.replace("__FEATURES__", feat_rows)

    usage_steps = "\n".join(
        f'''    <div class="step"><div class="num"></div><div class="body"><p>{ur}</p><p class="en">{ue}</p></div></div>'''
        for ur, ue in zip(a["USAGE"], a["USAGE_EN"])
    )
    html = html.replace("__USAGE__", usage_steps)

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

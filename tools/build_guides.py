#!/usr/bin/env python3
"""Render premium, deep bilingual (MSA Arabic + English) PDF user guides for
Construtech apps, matching the reference-guide design: cover with phone
mockups, full TOC with real page numbers, numbered section badges, a
workflow-pipeline diagram, per-section steps with real screenshots in phone
frames, tip/note/warning callouts, a feature table, an optional
material-comparison table, an FAQ, an install guide and a closing page.

Content for each app comes from tools/guide_content/<key>.json (written by
the exploration agents) + real screenshots in screenshots/<key>/guide/.

Usage: python3 build_guides.py [key1 key2 ...]   (default: all apps)
Requires: pip install playwright && playwright install chromium (already present)
"""
import datetime, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from app_data import applications

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONTENT_DIR = os.path.join(os.path.dirname(__file__), 'guide_content')
HTML_OUT = os.path.join(REPO_ROOT, 'tools', '_pdf_build')
PDF_OUT = os.path.join(REPO_ROOT, 'guides')
ROOT_URL = "file://" + REPO_ROOT

os.makedirs(HTML_OUT, exist_ok=True)
os.makedirs(PDF_OUT, exist_ok=True)

YEAR = str(datetime.date.today().year)

# Optional override of which 3 screenshots appear on an app's PDF cover
# (by default the first 3 files, alphabetically, from screenshots/<key>/guide/).
COVER_SHOTS = {
    "windoorgulf": ["wg6-quote.png", "wg8-roller3d.png", "wg9-arch-door.png"],
}
MIN_ANDROID = "7.0+"
PERMISSIONS_AR = "الإنترنت"
PERMISSIONS_EN = "Internet"

TIP_LABELS = {
    "note":    ("معلومة", "Note"),
    "tip":     ("نصيحة", "Tip"),
    "warning": ("تنبيه", "Warning"),
}
TIP_ICON = {"note": "ℹ️", "tip": "💡", "warning": "⚠️"}

def human_size(path):
    if not os.path.isfile(path):
        return "—"
    n = os.path.getsize(path)
    mb = n / (1024 * 1024)
    return f"{mb:.1f}MB" if mb >= 1 else f"{n // 1024}KB"


CSS = """
@font-face{font-family:'GE SS Two';font-weight:300;font-style:normal;unicode-range:U+0020-002F,U+003A-10FFFF;src:url('__ROOT__/fonts/GESSTwo-Light.otf') format('opentype')}
@font-face{font-family:'GE SS Two';font-weight:500;font-style:normal;unicode-range:U+0020-002F,U+003A-10FFFF;src:url('__ROOT__/fonts/GESSTwo-Medium.otf') format('opentype')}
@font-face{font-family:'GE SS Two';font-weight:700;font-style:normal;unicode-range:U+0020-002F,U+003A-10FFFF;src:url('__ROOT__/fonts/GESSTwo-Bold.otf') format('opentype')}
:root{ --primary:__PRIMARY__; --accent:__ACCENT__; --ink:#1a1d23; --muted:#5b6370; --line:#e3e6ea; --bg:#f6f7f9; }
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:'GE SS Two','Segoe UI',Tahoma,Arial,sans-serif;color:var(--ink);font-weight:300}
.en{font-family:'Segoe UI',Arial,sans-serif;direction:ltr;text-align:left;unicode-bidi:isolate}
.page{width:210mm;min-height:297mm;position:relative;overflow:hidden;page-break-after:always;display:flex;flex-direction:column}
.page:last-child{page-break-after:auto}
.pad{padding:16mm 16mm 22mm}

/* COVER */
.cover{background:linear-gradient(150deg,var(--primary) 0%,var(--accent) 115%);color:#fff;align-items:center;justify-content:center;text-align:center;position:relative}
.cover .deco{position:absolute;inset:0;opacity:.14;background-image:radial-gradient(circle at 10% 15%,#fff 0,transparent 22%),radial-gradient(circle at 90% 85%,#fff 0,transparent 26%),radial-gradient(circle at 85% 10%,#fff 0,transparent 14%)}
.cover .kicker{letter-spacing:4px;font-size:12px;opacity:.88;margin:0 0 26px;font-weight:600;position:relative;z-index:1}
.phones{display:flex;align-items:flex-end;justify-content:center;gap:-10px;position:relative;z-index:1;margin-bottom:30px}
.phone{width:46mm;border:5px solid #11131a;border-radius:16px;overflow:hidden;box-shadow:0 18px 44px rgba(0,0,0,.4);background:#000}
.phone img{width:100%;display:block}
.phone.side{width:36mm;opacity:.82;transform:translateY(8mm)}
.phone.side.l{margin-inline-end:-10mm}
.phone.side.r{margin-inline-start:-10mm}
.cover h1{font-size:44px;font-weight:700;margin:0 0 4px;position:relative;z-index:1}
.cover .guide-title{font-size:19px;font-weight:700;margin:16px 0 4px;position:relative;z-index:1}
.cover .guide-title .en{display:block;font-size:12.5px;font-weight:400;opacity:.85;text-align:center;margin-top:3px}
.cover .tagline{max-width:125mm;font-size:12.5px;line-height:1.85;opacity:.92;margin:14px 0 0;position:relative;z-index:1}
.cover .tagline .en{display:block;font-size:11px;opacity:.85;margin-top:7px;text-align:center}
.cover .ver-pill{margin-top:24px;display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.4);padding:7px 18px;border-radius:999px;font-size:12.5px;font-weight:600;position:relative;z-index:1}
.cover .brand{position:absolute;bottom:14mm;right:0;left:0;text-align:center;font-size:11.5px;opacity:.88;letter-spacing:2px;z-index:1}

/* HEADER / FOOTER */
.ph{display:flex;align-items:center;gap:12px;border-bottom:2px solid var(--primary);padding-bottom:13px;margin-bottom:18px}
.ph img{width:36px;height:36px;border-radius:9px}
.ph .t{font-size:15.5px;font-weight:700;color:var(--primary)}
.ph .t .en{font-size:10px;font-weight:400;color:var(--muted);margin-top:1px}
.ph .pill{margin-inline-start:auto;background:var(--bg);border:1px solid var(--line);font-size:10.5px;color:var(--muted);padding:4px 11px;border-radius:999px}
.pf{margin-top:auto;display:flex;justify-content:space-between;align-items:center;font-size:9.5px;color:var(--muted);border-top:1px solid var(--line);padding-top:8px}

.badge{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:50%;background:linear-gradient(145deg,var(--primary),var(--accent));color:#fff;font-size:14px;font-weight:700;flex:0 0 auto}
h2.sec{font-size:16.5px;font-weight:700;color:var(--primary);margin:0 0 4px;display:flex;align-items:center;gap:10px}
h2.sec .en{font-size:10.5px;font-weight:400;color:var(--muted)}
.sec-rule{height:3px;width:44px;background:var(--accent);border-radius:3px;margin:6px 0 16px}
.intro{font-size:12px;line-height:1.8;color:var(--ink);margin:0 0 14px}
.intro .en{margin-top:7px;font-size:10.5px;color:var(--muted)}

/* TOC */
.toc-list{margin-top:6px}
.toc-row{display:flex;align-items:baseline;gap:10px;padding:9px 0;border-bottom:1px dashed var(--line)}
.toc-row .num2{width:26px;height:26px;border-radius:50%;background:var(--bg);border:2px solid var(--accent);color:var(--primary);font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:0 0 auto}
.toc-row .ttl{font-size:12.5px;font-weight:700;flex:0 0 auto}
.toc-row .ttl .en{display:block;font-size:9.5px;font-weight:400;color:var(--muted)}
.toc-row .dots{flex:1;border-bottom:1px dotted var(--line);margin:0 6px;transform:translateY(-4px)}
.toc-row .pg{font-size:12px;font-weight:700;color:var(--primary)}

/* AUDIENCE / FACTS */
.audience-box{background:var(--bg);border-radius:14px;padding:16px 18px;margin-bottom:18px;border-inline-start:4px solid var(--accent)}
.audience-box p{margin:0;font-size:12.5px;line-height:1.85}
.audience-box p.en{margin-top:9px;font-size:10.5px;color:var(--muted);padding-top:9px;border-top:1px dashed var(--line)}
.facts-strip{display:flex;gap:9px;margin-top:6px}
.fact{flex:1;background:var(--primary);color:#fff;border-radius:11px;padding:10px 6px;text-align:center}
.fact b{display:block;font-size:12px}
.fact span{display:block;font-size:8.5px;opacity:.88;margin-top:3px}
.fact span.en{direction:ltr;margin-top:1px}

/* PIPELINE */
.pipeline{display:flex;align-items:center;justify-content:center;gap:4px;margin:26px 0 10px;flex-wrap:wrap}
.pl-node{display:flex;flex-direction:column;align-items:center;width:30mm}
.pl-node .ic{width:56px;height:56px;border-radius:50%;background:linear-gradient(145deg,var(--primary),var(--accent));color:#fff;display:flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 8px 18px rgba(0,0,0,.18)}
.pl-node .tt{margin-top:9px;font-size:11px;font-weight:700;text-align:center;line-height:1.4}
.pl-node .tt .en{display:block;font-size:9px;font-weight:400;color:var(--muted);margin-top:2px}
.pl-arrow{font-size:20px;color:var(--accent);margin:0 -2px 30px}

/* SECTION STEPS w/ screenshots */
.step{display:flex;gap:14px;align-items:flex-start;margin-bottom:16px}
.step .num{width:30px;height:30px;border-radius:50%;flex:0 0 auto;background:linear-gradient(145deg,var(--primary),var(--accent));color:#fff;display:flex;align-items:center;justify-content:center;font-size:12.5px;font-weight:700}
.step .body{flex:1;padding-top:2px}
.step .body p{margin:0;font-size:12px;line-height:1.7}
.step .body p.en{margin-top:4px;font-size:10px;color:var(--muted)}
.step .shot{flex:0 0 auto;width:30mm;border:4px solid var(--ink);border-radius:13px;overflow:hidden;box-shadow:0 8px 20px rgba(0,0,0,.18)}
.step .shot img{width:100%;display:block}

.tip-box{margin-top:10px;border-radius:12px;padding:12px 15px;font-size:11px;line-height:1.75;display:flex;gap:10px;align-items:flex-start}
.tip-box .ic{font-size:16px}
.tip-box .en{margin-top:5px;font-size:9.5px;opacity:.9}
.tip-note{background:#eaf2fb;border:1px solid #cfe2f6;color:#1a4a73}
.tip-tip{background:#eaf7f0;border:1px solid #cdecd9;color:#1a5c3a}
.tip-warning{background:#fdeeea;border:1px solid #f7cfc2;color:#8a2f17}

/* FEATURE TABLE */
.ftable{width:100%;border-collapse:collapse;font-size:11px}
.ftable th{background:var(--primary);color:#fff;text-align:start;padding:9px 12px;font-size:10.5px}
.ftable td{padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}
.ftable tr:nth-child(even) td{background:var(--bg)}
.ftable .en{display:block;margin-top:3px;font-size:9.5px;color:var(--muted)}

/* COMPARISON */
.cmp{width:100%;border-collapse:collapse;font-size:11px;margin-top:4px}
.cmp th{background:var(--bg);color:var(--primary);text-align:center;padding:10px;border:1px solid var(--line);font-size:11px}
.cmp td{padding:10px;border:1px solid var(--line);text-align:center;vertical-align:top}
.cmp .en{display:block;margin-top:3px;font-size:9.5px;color:var(--muted)}
.cmp td:first-child,.cmp th:first-child{background:var(--bg);font-weight:700;text-align:start}

/* FAQ */
.faq-item{margin-bottom:14px}
.faq-q{display:flex;gap:9px;align-items:flex-start;font-weight:700;font-size:12px}
.faq-q .qm{width:22px;height:22px;border-radius:50%;background:var(--accent);color:#fff;flex:0 0 auto;display:flex;align-items:center;justify-content:center;font-size:12px}
.faq-q .en{display:block;font-weight:400;font-size:10px;color:var(--muted);margin-top:2px}
.faq-a{margin:7px 0 0 31px;font-size:11px;line-height:1.75;color:var(--ink)}
.faq-a .en{margin-top:4px;font-size:10px;color:var(--muted)}

.no-shots{background:var(--bg);border-radius:14px;padding:22px;text-align:center;color:var(--muted);font-size:11.5px;line-height:1.85}
.contact-grid{display:flex;gap:12px;margin-top:10px}
.contact-grid{flex-wrap:wrap}
.contact-card{flex:1 1 28%;min-width:28%;background:var(--bg);border-radius:12px;padding:12px 8px;text-align:center;border:1px solid var(--line)}
.contact-card .ic{font-size:18px;margin-bottom:5px}
.contact-card b{display:block;font-size:10.5px;word-break:break-word}
.contact-card .en{display:block;font-size:8.5px;color:var(--muted);margin-top:4px;direction:rtl;text-align:center}
.qr-box{display:flex;align-items:center;gap:16px;background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-top:12px}
.qr-box img{width:76px;height:76px;border-radius:9px;background:#fff;border:1px solid var(--line);flex:0 0 auto}
.qr-box .qt{font-size:11px;line-height:1.7}
.qr-box .qt b{display:block;font-size:12px;margin-bottom:3px}
.qr-box .qt .en{margin-top:3px;font-size:9.5px;color:var(--muted)}
"""

def esc(s):
    return s if s else ""

def bi(d, cls=""):
    """bilingual <p>ar<span class=en>en</span></p>-ish helper returns (ar, en) tuple safely"""
    return esc(d.get("ar")), esc(d.get("en"))

def page_header(name, logo, title_ar, title_en, version):
    return f'''<div class="ph"><img src="{ROOT_URL}/logos/{logo}"><div class="t">{title_ar}<div class="en">{title_en}</div></div><div class="pill">{version}</div></div>'''

def page_footer(name, version, pageno):
    return f'''<div class="pf"><span>Construtech <span class="en">© {YEAR}</span></span><span>{name} {version} — {pageno}</span></div>'''

def render_cover(a, content, shots_dir, shots):
    name, logo, version = a["NAME"], a["LOGO"], a["VERSION"]
    tagline_ar, tagline_en = bi(content.get("overview", {}))
    tagline_ar = (tagline_ar[:140] + "…") if len(tagline_ar) > 140 else tagline_ar
    tagline_en = (tagline_en[:160] + "…") if len(tagline_en) > 160 else tagline_en
    pick = shots[:3] if len(shots) >= 3 else (shots * 3)[:3] if shots else []
    phones = ""
    if len(pick) == 3:
        s0, s1, s2 = pick
        phones = f'''<div class="phones">
          <div class="phone side l"><img src="{ROOT_URL}/screenshots/{a['_key']}/guide/{s0}"></div>
          <div class="phone"><img src="{ROOT_URL}/screenshots/{a['_key']}/guide/{s1}"></div>
          <div class="phone side r"><img src="{ROOT_URL}/screenshots/{a['_key']}/guide/{s2}"></div>
        </div>'''
    return f'''<section class="page cover">
      <div class="deco"></div>
      <p class="kicker">CONSTRUTECH</p>
      {phones}
      <h1>{name}</h1>
      <p class="guide-title">دليل الاستخدام الشامل<span class="en">Complete User Guide</span></p>
      <p class="tagline">{tagline_ar}<span class="en">{tagline_en}</span></p>
      <div class="ver-pill">📦 {version}</div>
      <div class="brand">CONSTRUTECH · {YEAR}</div>
    </section>'''

def render_toc(a, toc_entries):
    name, logo, version = a["NAME"], a["LOGO"], a["VERSION"]
    rows = "\n".join(
        f'''<div class="toc-row"><div class="num2">{i+1}</div>
            <div class="ttl">{t_ar}<span class="en">{t_en}</span></div>
            <div class="dots"></div><div class="pg">{pg}</div></div>'''
        for i, (t_ar, t_en, pg) in enumerate(toc_entries)
    )
    return f'''<section class="page pad">
      {page_header(name, logo, "المحتويات", "Table of contents", version)}
      <div class="toc-list">{rows}</div>
      {page_footer(name, version, 2)}
    </section>'''

def render_overview(a, content, pageno):
    name, logo, version = a["NAME"], a["LOGO"], a["VERSION"]
    ov_ar, ov_en = bi(content.get("overview", {}))
    au_ar, au_en = bi(content.get("audience", {}))
    apk_path = os.path.join(REPO_ROOT, 'apks', a["APK"])
    facts = [
        ("📦", human_size(apk_path), "الحجم", "Size"),
        ("🤖", MIN_ANDROID, "أندرويد", "Android"),
        ("🌐", PERMISSIONS_AR, "الصلاحيات", "Permissions"),
        ("🏷️", "Construtech", "المطوّر", "Developer"),
    ]
    facts_html = "\n".join(
        f'<div class="fact"><b>{ic} {val}</b><span>{lbl_ar}</span><span class="en">{lbl_en}</span></div>'
        for ic, val, lbl_ar, lbl_en in facts
    )
    gulf_box = ""
    gd = content.get("gulf_differences")
    if gd and gd.get("ar"):
        gd_ar, gd_en = bi(gd)
        gulf_box = f'''<div class="audience-box" style="margin-top:14px"><p><b>الفروقات الخاصة بنسخة الخليج:</b> {gd_ar}</p><p class="en"><b>Gulf-edition differences:</b> {gd_en}</p></div>'''
    return f'''<section class="page pad">
      {page_header(name, logo, "نظرة عامة على التطبيق", "App overview", version)}
      <h2 class="sec">ما هو {name}؟<span class="en">What is {name}?</span></h2>
      <div class="sec-rule"></div>
      <p class="intro">{ov_ar}<span class="en">{ov_en}</span></p>
      <h2 class="sec">الفئة المستهدفة<span class="en">Who it's for</span></h2>
      <div class="sec-rule"></div>
      <div class="audience-box"><p>{au_ar}</p><p class="en">{au_en}</p></div>
      {gulf_box}
      <div class="facts-strip">{facts_html}</div>
      {page_footer(name, version, pageno)}
    </section>'''

def render_pipeline(a, content, pageno):
    name, logo, version = a["NAME"], a["LOGO"], a["VERSION"]
    nodes = content.get("workflow_pipeline", [])
    parts = []
    for i, n in enumerate(nodes):
        t_ar, t_en = bi(n.get("title", {}))
        parts.append(f'<div class="pl-node"><div class="ic">{esc(n.get("icon","•"))}</div><div class="tt">{t_ar}<span class="en">{t_en}</span></div></div>')
        if i < len(nodes) - 1:
            parts.append('<div class="pl-arrow">←</div>')
    return f'''<section class="page pad">
      {page_header(name, logo, "مخطط سير العمل", "Workflow pipeline", version)}
      <h2 class="sec">كيف تسير العملية من البداية إلى النهاية<span class="en">How the process flows end-to-end</span></h2>
      <div class="sec-rule"></div>
      <div class="pipeline">{''.join(parts)}</div>
      {page_footer(name, version, pageno)}
    </section>'''

def render_section_page(a, sec, idx, pageno, cont=False):
    name, logo, version = a["NAME"], a["LOGO"], a["VERSION"]
    t_ar, t_en = bi(sec.get("title", {}))
    intro_ar, intro_en = bi(sec.get("intro", {}))
    steps_html = []
    start_n = sec.get("_step_start_num", 1)
    for i, s in enumerate(sec.get("_steps_chunk", [])):
        s_ar, s_en = bi(s.get("text", {}))
        shot = s.get("screenshot")
        shot_html = f'<div class="shot"><img src="{ROOT_URL}/screenshots/{a["_key"]}/guide/{shot}"></div>' if shot else ""
        steps_html.append(f'<div class="step"><div class="num">{start_n + i}</div><div class="body"><p>{s_ar}</p><p class="en">{s_en}</p></div>{shot_html}</div>')
    tip_html = ""
    tip = sec.get("tip")
    if tip and not cont:
        kind = tip.get("type", "note")
        ar_lbl, en_lbl = TIP_LABELS.get(kind, TIP_LABELS["note"])
        tip_ar, tip_en = bi(tip)
        tip_html = f'''<div class="tip-box tip-{kind}"><div class="ic">{TIP_ICON.get(kind,"ℹ️")}</div><div><b>{ar_lbl}:</b> {tip_ar}<div class="en"><b>{en_lbl}:</b> {tip_en}</div></div></div>'''
    cont_mark_ar = " (تابع)" if cont else ""
    cont_mark_en = " (cont'd)" if cont else ""
    return f'''<section class="page pad">
      {page_header(name, logo, f"{t_ar}{cont_mark_ar}", f"{t_en}{cont_mark_en}", version)}
      <h2 class="sec"><span class="badge">{idx}</span>{t_ar}<span class="en">{t_en}</span></h2>
      <div class="sec-rule"></div>
      {'<p class="intro">' + intro_ar + '<span class="en">' + intro_en + '</span></p>' if intro_ar and not cont else ''}
      {''.join(steps_html)}
      {tip_html}
      {page_footer(name, version, pageno)}
    </section>'''

def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def render_feature_pages(a, rows, start_pageno):
    name, logo, version = a["NAME"], a["LOGO"], a["VERSION"]
    pages = []
    chunks = list(chunk(rows, 11)) or [[]]
    for ci, c in enumerate(chunks):
        trs = "\n".join(
            f'''<tr><td>{esc(r["feature"]["ar"])}<span class="en">{esc(r["feature"]["en"])}</span></td>
                 <td>{esc(r["detail"]["ar"])}<span class="en">{esc(r["detail"]["en"])}</span></td></tr>'''
            for r in c
        )
        title_suffix_ar = " (تابع)" if ci else ""
        title_suffix_en = " (cont'd)" if ci else ""
        pages.append(f'''<section class="page pad">
          {page_header(name, logo, f"جميع المزايا{title_suffix_ar}", f"All features{title_suffix_en}", version)}
          <h2 class="sec">ما يقدمه التطبيق<span class="en">What the app offers</span></h2>
          <div class="sec-rule"></div>
          <table class="ftable"><tr><th>الميزة / Feature</th><th>التفصيل / Detail</th></tr>{trs}</table>
          {page_footer(name, version, start_pageno + ci)}
        </section>''')
    return pages

def render_comparison_page(a, rows, pageno):
    if not rows:
        return None
    name, logo, version = a["NAME"], a["LOGO"], a["VERSION"]
    aspect0_ar = esc(rows[0].get("option_a", {}).get("ar", "الخيار الأول"))
    trs = "\n".join(
        f'''<tr><td>{esc(r["aspect"]["ar"])}<span class="en">{esc(r["aspect"]["en"])}</span></td>
             <td>{esc(r["option_a"]["ar"])}<span class="en">{esc(r["option_a"]["en"])}</span></td>
             <td>{esc(r["option_b"]["ar"])}<span class="en">{esc(r["option_b"]["en"])}</span></td></tr>'''
        for r in rows
    )
    return f'''<section class="page pad">
      {page_header(name, logo, "مقارنة بين الخيارات", "Options comparison", version)}
      <h2 class="sec">خصوصيات كل خيار<span class="en">Specifics of each option</span></h2>
      <div class="sec-rule"></div>
      <table class="cmp"><tr><th>الجانب / Aspect</th><th>الخيار الأول / Option A</th><th>الخيار الثاني / Option B</th></tr>{trs}</table>
      {page_footer(name, version, pageno)}
    </section>'''

def render_faq_pages(a, faq, start_pageno):
    name, logo, version = a["NAME"], a["LOGO"], a["VERSION"]
    pages = []
    chunks = list(chunk(faq, 5)) or [[]]
    for ci, c in enumerate(chunks):
        items = "\n".join(
            f'''<div class="faq-item"><div class="faq-q"><div class="qm">؟</div><div>{esc(f["q"]["ar"])}<span class="en">{esc(f["q"]["en"])}</span></div></div>
                <div class="faq-a">{esc(f["a"]["ar"])}<span class="en">{esc(f["a"]["en"])}</span></div></div>'''
            for f in c
        )
        title_suffix_ar = " (تابع)" if ci else ""
        title_suffix_en = " (cont'd)" if ci else ""
        pages.append(f'''<section class="page pad">
          {page_header(name, logo, f"الأسئلة الشائعة{title_suffix_ar}", f"FAQ{title_suffix_en}", version)}
          <h2 class="sec">أسئلة متكررة<span class="en">Frequently asked questions</span></h2>
          <div class="sec-rule"></div>
          {items}
          {page_footer(name, version, start_pageno + ci)}
        </section>''')
    return pages

def render_install_page(a, pageno):
    name, logo, version = a["NAME"], a["LOGO"], a["VERSION"]
    steps = [
        ("قم بتحميل ملف APK من صفحة التطبيق.", "Download the APK file from the app's page."),
        ('إذا ظهر تنبيه "التثبيت من مصادر غير معروفة"، توجّه إلى الإعدادات وفعّل ذلك لمتصفحك (مرة واحدة فقط).',
         'If you see an "install from unknown sources" warning, go to Settings and allow it for your browser (just once).'),
        ("عد إلى ملف APK الذي حمّلته وافتحه، ثم اضغط تثبيت.", "Go back to the downloaded APK file, open it, then tap Install."),
        ('بعد التثبيت، يمكنك إلغاء السماح بـ "مصادر غير معروفة" إن رغبت.', 'After installing, you can turn the "unknown sources" permission back off if you like.'),
    ]
    steps_html = "\n".join(
        f'<div class="step"><div class="num">{i+1}</div><div class="body"><p>{ar}</p><p class="en">{en}</p></div></div>'
        for i, (ar, en) in enumerate(steps)
    )
    return f'''<section class="page pad">
      {page_header(name, logo, "طريقة تثبيت التطبيق", "Installing the app", version)}
      <h2 class="sec">التثبيت (خارج المتجر)<span class="en">Install (outside the store)</span></h2>
      <div class="sec-rule"></div>
      {steps_html}
      <div class="tip-box tip-warning"><div class="ic">⚠️</div><div><b>تنبيه:</b> هذا التطبيق غير متوفر على Google Play — فهو تحميل مباشر (APK). تأكد دائمًا من مصدر الملف قبل تثبيت أي تطبيق على هاتفك.
        <div class="en"><b>Warning:</b> this app isn't on Google Play — it's a direct APK download. Always verify the file's source before installing any app on your phone.</div></div></div>
      <div class="qr-box">
        <img src="{ROOT_URL}/qrcodes/{a['_key']}.png">
        <div class="qt"><b>📷 مسح سريع للتثبيت المباشر</b>صوّر هذا الرمز بكاميرا هاتفك ليبدأ تحميل {name} {version} فورًا.
        <div class="en"><b>Quick scan to install directly</b>Scan this code with your phone's camera to start downloading {name} {version} right away.</div></div>
      </div>
      {page_footer(name, version, pageno)}
    </section>'''

CONTACT_LABELS = {
    "developer": ("المطوّر", "Developer", "🏷️"),
    "phone": ("الهاتف", "Phone", "📞"),
    "whatsapp": ("واتساب", "WhatsApp", "💬"),
    "email": ("البريد الإلكتروني", "Email", "✉️"),
    "rip": ("الحساب البريدي (RIP)", "Bank account (RIP)", "🏦"),
    "rip_account_name": ("اسم صاحب الحساب", "Account holder", "👤"),
}

def render_closing_page(a, content, pageno):
    name, logo, version = a["NAME"], a["LOGO"], a["VERSION"]
    contact = content.get("real_contact_info_found_in_app")
    contact_html = ""
    plans_html = ""
    if contact and isinstance(contact, dict):
        cards = []
        for k, v in contact.items():
            if k in ("note", "note_ar", "note_en", "subscription_plans_dzd", "payment_methods") or not v:
                continue
            lbl_ar, lbl_en, ic = CONTACT_LABELS.get(k, (k, k, "ℹ️"))
            cards.append(f'<div class="contact-card"><div class="ic">{ic}</div><b>{esc(str(v))}</b><span class="en">{lbl_ar} / {lbl_en}</span></div>')
        if cards:
            contact_html = f'<h2 class="sec">للتواصل والدعم<span class="en">Contact &amp; support</span></h2><div class="sec-rule"></div><div class="contact-grid">{"".join(cards)}</div>'
        plans = contact.get("subscription_plans_dzd")
        if plans:
            PLAN_LABELS = {
                "3_months": "3 أشهر", "6_months": "6 أشهر", "12_months": "12 شهرًا",
                "lifetime": "مدى الحياة", "1_month": "شهر واحد",
            }
            def plan_label(k):
                return PLAN_LABELS.get(k, k.replace("_", " "))
            rows = "".join(f'<tr><td>{esc(plan_label(p))}</td><td>{esc(str(price))} دج</td></tr>' for p, price in plans.items())
            plans_html = f'<h2 class="sec" style="margin-top:16px">خطط الاشتراك<span class="en">Subscription plans</span></h2><div class="sec-rule"></div><table class="ftable"><tr><th>المدة</th><th>السعر</th></tr>{rows}</table>'
    elif contact:
        contact_html = f'<h2 class="sec">للتواصل والدعم<span class="en">Contact &amp; support</span></h2><div class="sec-rule"></div><div class="contact-grid"><div class="contact-card"><div class="ic">📞</div><b>{esc(str(contact))}</b></div></div>'
    return f'''<section class="page pad">
      {page_header(name, logo, "شكرًا لاستخدامك التطبيق", "Thank you for using the app", version)}
      <h2 class="sec">خلاصة<span class="en">Wrap-up</span></h2>
      <div class="sec-rule"></div>
      <div class="audience-box"><p>نتمنى أن يكون هذا الدليل قد غطّى كل ما يلزمك لاستخدام {name} بثقة وفعالية. راجع هذا الدليل كلما احتجت إلى تذكّر خطوة معينة.</p>
      <p class="en">We hope this guide has covered everything you need to use {name} confidently and efficiently. Come back to it any time you need a reminder of a particular step.</p></div>
      {contact_html}
      {plans_html}
      {page_footer(name, version, pageno)}
    </section>'''


def build_one(key):
    a = dict(applications[key])
    a["_key"] = key
    content_path = os.path.join(CONTENT_DIR, f"{key}.json")
    if not os.path.isfile(content_path):
        print(f"SKIP {key}: no content file at {content_path}")
        return None
    content = json.load(open(content_path, encoding='utf-8'))

    shots_dir = os.path.join(REPO_ROOT, 'screenshots', key, 'guide')
    shots = sorted(os.listdir(shots_dir)) if os.path.isdir(shots_dir) else []

    # Prepare section chunks (max 3 steps per page)
    sections = content.get("sections", [])
    section_pages_meta = []  # list of (section, chunk_steps, is_cont)
    for sec in sections:
        steps = sec.get("steps", [])
        step_chunks = list(chunk(steps, 3)) or [[]]
        for i, sc in enumerate(step_chunks):
            s2 = dict(sec)
            s2["_steps_chunk"] = sc
            s2["_step_start_num"] = i * 3 + 1
            section_pages_meta.append((s2, i > 0))

    feature_rows = content.get("feature_table", [])
    n_feature_pages = max(1, -(-len(feature_rows) // 11)) if feature_rows else 0
    cmp_rows = content.get("material_comparison_table", [])
    n_cmp_pages = 1 if cmp_rows else 0
    faq_rows = content.get("faq", [])
    n_faq_pages = max(1, -(-len(faq_rows) // 5)) if faq_rows else 0

    # page numbering: 1=cover(unnumbered visually), 2=TOC, 3=overview, 4=pipeline,
    # then sections, then features, then comparison, then faq, then install, then closing
    p = 3
    toc_entries = []
    pageno_overview = p; p += 1
    toc_entries.append(("نظرة عامة", "Overview", pageno_overview))
    pageno_pipeline = p; p += 1
    toc_entries.append(("مخطط سير العمل", "Workflow pipeline", pageno_pipeline))

    section_pagenos = []
    sec_idx = 0
    last_title = None
    for sec, is_cont in section_pages_meta:
        section_pagenos.append(p)
        if not is_cont:
            sec_idx += 1
            t_ar, t_en = bi(sec.get("title", {}))
            toc_entries.append((t_ar, t_en, p))
        p += 1

    pageno_features = p
    if n_feature_pages:
        toc_entries.append(("جميع المزايا", "All features", p))
    p += n_feature_pages

    pageno_cmp = p
    if n_cmp_pages:
        toc_entries.append(("مقارنة بين الخيارات", "Options comparison", p))
    p += n_cmp_pages

    pageno_faq = p
    if n_faq_pages:
        toc_entries.append(("الأسئلة الشائعة", "FAQ", p))
    p += n_faq_pages

    pageno_install = p
    toc_entries.append(("طريقة التثبيت", "Installing the app", p))
    p += 1
    pageno_closing = p
    toc_entries.append(("خلاصة", "Wrap-up", p))
    p += 1

    pages_html = []
    cover_shots = COVER_SHOTS.get(key, shots)
    pages_html.append(render_cover(a, content, shots_dir, cover_shots))
    pages_html.append(render_toc(a, toc_entries))
    pages_html.append(render_overview(a, content, pageno_overview))
    pages_html.append(render_pipeline(a, content, pageno_pipeline))

    sec_idx = 0
    for (sec, is_cont), pageno in zip(section_pages_meta, section_pagenos):
        if not is_cont:
            sec_idx += 1
        pages_html.append(render_section_page(a, sec, sec_idx, pageno, cont=is_cont))

    if feature_rows:
        pages_html.extend(render_feature_pages(a, feature_rows, pageno_features))
    if cmp_rows:
        cp = render_comparison_page(a, cmp_rows, pageno_cmp)
        if cp:
            pages_html.append(cp)
    if faq_rows:
        pages_html.extend(render_faq_pages(a, faq_rows, pageno_faq))
    pages_html.append(render_install_page(a, pageno_install))
    pages_html.append(render_closing_page(a, content, pageno_closing))

    css = CSS.replace("__PRIMARY__", a["COLOR"]["primary"]).replace("__ACCENT__", a["COLOR"]["accent"]).replace("__ROOT__", ROOT_URL)
    html = f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><style>{css}</style></head><body>
{"".join(pages_html)}
</body></html>'''

    out_html = os.path.join(HTML_OUT, f"{key}.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    return out_html


def main():
    keys = sys.argv[1:] or list(applications.keys())
    built = {}
    for key in keys:
        path = build_one(key)
        if path:
            built[key] = path

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        for key, path in built.items():
            pg = b.new_page()
            pg.goto("file://" + path)
            pg.wait_for_timeout(300)
            pg.pdf(
                path=os.path.join(PDF_OUT, f"{key}-guide.pdf"),
                format="A4",
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
            pg.close()
            print("built guide:", key)
        b.close()

if __name__ == "__main__":
    main()

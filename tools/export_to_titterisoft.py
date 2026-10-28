"""Export one or all apps' full download-page system (page + APK + PDF guide +
screenshots + QR code) from kozin-ads into a titterisoft-website checkout,
as a self-contained bundle under its public/ folder (served verbatim by
Cloudflare Pages, same URL structure as kozin-ads: /apps/<key>.html,
/apks/<APK>, /guides/<key>-guide.pdf, /screenshots/<key>/*, /qrcodes/<key>.png).

This is a faithful copy of build_apps.py's page template, with two
differences: the QR code is re-rendered to point at the titterisoft domain
instead of kozin-ads, and the @font-face rules point at titterisoft's own
already-hosted GE SS Two webfonts instead of shipping a second otf copy.

Usage:
  python3 export_to_titterisoft.py --dest /path/to/titterisoft-website [--key windoor] [--base-url https://tettrisoft.pages.dev]

Requires: the app's current apk/guide/screenshots already present under
kozin-ads's own apks/, guides/, screenshots/<key>/ (i.e. run update_app.py
first when syncing a single app after a fresh build).
"""
import argparse, ctypes, os, sys, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from app_data import applications  # noqa: E402

DEFAULT_BASE_URL = "https://tettrisoft.pages.dev"

MIN_ANDROID = "Android 7.0 أو أحدث"
PERMISSIONS = "الإنترنت فقط"


def human_size(path):
    if not os.path.isfile(path):
        return None
    n = os.path.getsize(path)
    mb = n / (1024 * 1024)
    if mb >= 1:
        return f"{mb:.1f} ميغابايت"
    return f"{n // 1024} كيلوبايت"


# Same template as build_apps.py, except: fonts come from the main
# titterisoft site's own webfonts (absolute path), not a duplicated ../fonts/.
TPL = '''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>__NAME__ __VERSION__ — تحميل وتعريف</title>
<meta name="description" content="__NAME__ — __TAGLINE__">
<style>
  :root{
    --bg:#f6f7f9; --card:#ffffff; --text:#1a1d23; --muted:#5b6370;
    --line:#e6e8ec; --brand:#1a56db; --brand-dark:#123f9e;
    --install:#0f9d58; --install-dark:#0b8043;
  }
  @media (prefers-color-scheme: dark){
    :root:not([data-theme="light"]){
      --bg:#0f1115; --card:#181b21; --text:#eef0f3; --muted:#9aa3b2;
      --line:#262a33; --brand:#4d8dff; --brand-dark:#6ea2ff;
      --install:#2fb36c; --install-dark:#3fc97f;
    }
  }
  :root[data-theme="dark"]{
    --bg:#0f1115; --card:#181b21; --text:#eef0f3; --muted:#9aa3b2;
    --line:#262a33; --brand:#4d8dff; --brand-dark:#6ea2ff;
    --install:#2fb36c; --install-dark:#3fc97f;
  }
  @font-face{font-family:'GE SS Two';font-weight:300;font-style:normal;font-display:swap;unicode-range:U+0020-002F,U+003A-10FFFF;src:url('/assets/fonts/ge-ss-two-light.woff') format('woff')}
  @font-face{font-family:'GE SS Two';font-weight:500;font-style:normal;font-display:swap;unicode-range:U+0020-002F,U+003A-10FFFF;src:url('/assets/fonts/ge-ss-two-medium.woff') format('woff')}
  @font-face{font-family:'GE SS Two';font-weight:700;font-style:normal;font-display:swap;unicode-range:U+0020-002F,U+003A-10FFFF;src:url('/assets/fonts/ge-ss-two-bold.woff') format('woff')}
  *{box-sizing:border-box}
  body{margin:0; background:var(--bg); color:var(--text); font-family:'GE SS Two','Segoe UI',Tahoma,Arial,sans-serif; line-height:1.7}

  .hero{
    max-width:800px; margin:0 auto; padding:34px 16px 20px;
    display:flex; flex-direction:row-reverse; align-items:flex-start; justify-content:center; gap:20px; text-align:right;
  }
  .hero img.icon{
    width:112px; height:112px; border-radius:24px; border:1px solid var(--line); flex:0 0 auto;
    box-shadow:0 2px 10px rgba(0,0,0,.08);
  }
  .hero .info{padding-top:2px}
  .hero h1{margin:0 0 6px; font-size:25px; line-height:1.3}
  .hero .dev{color:var(--brand); font-size:14px; margin:0 0 8px; font-weight:600}
  .hero .meta-row{display:flex; gap:10px; align-items:center; color:var(--muted); font-size:12.5px; margin:0}
  .hero .meta-row .dot{width:3px; height:3px; border-radius:50%; background:var(--muted)}
  .updated-badge{
    display:none; align-items:center; gap:6px; margin:10px 0 0;
    background:var(--install); color:#fff; font-size:12.5px; font-weight:600;
    padding:5px 12px; border-radius:999px; width:fit-content;
  }

  .quickfacts{
    max-width:800px; margin:0 auto; padding:2px 16px 16px;
    display:flex; justify-content:center; gap:22px; flex-wrap:wrap;
  }
  .quickfacts .qf{display:flex; flex-direction:column; align-items:center; gap:3px; min-width:64px}
  .quickfacts .qf .ic{font-size:17px}
  .quickfacts .qf b{color:var(--text); font-size:13px; font-weight:700}
  .quickfacts .qf span{color:var(--muted); font-size:11.5px}

  .hero-actions{max-width:800px; margin:0 auto; padding:14px 16px 8px; display:flex; justify-content:center; gap:10px; flex-wrap:wrap}
  .dl-btn{
    display:inline-flex; align-items:center; gap:8px; background:var(--install); color:#fff;
    text-decoration:none; padding:13px 30px; border-radius:24px; font-size:15px; font-weight:700;
  }
  .dl-btn:hover{background:var(--install-dark)}
  .pdf-btn{
    display:inline-flex; align-items:center; gap:8px; background:var(--card); color:var(--text);
    text-decoration:none; padding:13px 22px; border-radius:24px; font-size:15px; font-weight:600;
    border:1px solid var(--line);
  }
  .pdf-btn:hover{border-color:var(--brand); color:var(--brand)}
  .dl-hint{max-width:800px; margin:0 auto; padding:0 16px; text-align:center; color:var(--muted); font-size:12px}

  @keyframes pulseGlow{
    0%{box-shadow:0 0 0 0 rgba(15,157,88,.45)}
    70%{box-shadow:0 0 0 14px rgba(15,157,88,0)}
    100%{box-shadow:0 0 0 0 rgba(15,157,88,0)}
  }
  section.install-steps.pulse{animation:pulseGlow 1.4s ease-out 2; border-color:var(--install)}

  .tagline-wrap{max-width:800px; margin:0 auto; padding:6px 16px 10px; text-align:center}
  .tagline-wrap p{color:var(--muted); font-size:15px; margin:0 auto; max-width:560px}

  .shots{max-width:800px; margin:0 auto; padding:10px 0 26px}
  .shots-row{display:flex; gap:12px; overflow-x:auto; padding:4px 16px 8px; scroll-snap-type:x proximity; justify-content:center}
  .shots-row img{
    height:360px; border-radius:16px; border:1px solid var(--line); scroll-snap-align:start; flex:0 0 auto;
    background:var(--card);
  }
  .shots-empty{
    max-width:800px; margin:0 auto 10px; padding:14px 16px; color:var(--muted); font-size:13px;
  }

  main{max-width:800px; margin:0 auto; padding:0 16px 60px}
  section{background:var(--card); border:1px solid var(--line); border-radius:14px; padding:22px 24px; margin-bottom:16px}
  section h2{margin:0 0 14px; font-size:17px}
  section > p.lead{margin:0 0 14px; color:var(--muted); font-size:13.5px}

  .highlights{display:grid; grid-template-columns:repeat(auto-fit, minmax(190px,1fr)); gap:14px}
  .hl-card{background:var(--bg); border:1px solid var(--line); border-radius:12px; padding:16px}
  .hl-card .ic{font-size:26px; margin-bottom:8px; display:block}
  .hl-card h3{margin:0 0 6px; font-size:14.5px}
  .hl-card p{margin:0; color:var(--muted); font-size:13px}

  .audience p{margin:0; font-size:14.5px; color:var(--text)}

  .chips{display:flex; flex-wrap:wrap; gap:8px}
  .chip{background:var(--bg); border:1px solid var(--line); border-radius:999px; padding:6px 13px; font-size:13.5px; color:var(--text)}

  .infotable{width:100%; border-collapse:collapse}
  .infotable tr{border-bottom:1px solid var(--line)}
  .infotable tr:last-child{border-bottom:none}
  .infotable td{padding:11px 4px; font-size:14px; vertical-align:top}
  .infotable td:first-child{color:var(--muted); width:38%}
  .infotable td:last-child{font-weight:600}

  .faq details{border-bottom:1px solid var(--line); padding:12px 0}
  .faq details:last-child{border-bottom:none}
  .faq summary{cursor:pointer; font-weight:600; font-size:14.5px; list-style:none; display:flex; justify-content:space-between; align-items:center; gap:10px}
  .faq summary::-webkit-details-marker{display:none}
  .faq summary::after{content:'+'; font-size:19px; color:var(--muted); flex:0 0 auto}
  .faq details[open] summary::after{content:'−'}
  .faq p{margin:10px 0 0; color:var(--muted); font-size:13.5px}

  ol{margin:0; padding-right:20px}
  li{margin-bottom:9px; font-size:14.5px}
  .note{margin-top:14px; font-size:13px; color:var(--muted); border-top:1px dashed var(--line); padding-top:12px}
  footer{text-align:center; padding:24px 16px; color:var(--muted); font-size:12.5px}

  .qr-box{display:flex; align-items:center; gap:18px; background:var(--bg); border:1px solid var(--line); border-radius:14px; padding:16px 18px; margin-top:16px}
  .qr-box img{width:108px; height:108px; border-radius:10px; background:#fff; flex:0 0 auto; border:1px solid var(--line)}
  .qr-box .qt{font-size:13.5px}
  .qr-box .qt b{display:block; font-size:14.5px; margin-bottom:4px}
  .qr-box .qt span{color:var(--muted); font-size:12.5px}
</style>
</head>
<body>

<div class="hero">
  <img class="icon" src="../logos/__LOGO__" alt="شعار __NAME__">
  <div class="info">
    <h1>__NAME__</h1>
    <p class="dev">Construtech</p>
    <p class="meta-row"><span>__VERSION__</span><span class="dot"></span><span>Android</span><span class="dot"></span><span>APK مباشر</span></p>
    <p class="updated-badge" id="updatedBadge" data-updated="__UPDATED__">🆕 تم تحديث التطبيق مؤخرًا</p>
  </div>
</div>

<div class="tagline-wrap"><p>__TAGLINE__</p></div>

<div class="quickfacts">
  <div class="qf"><span class="ic">📦</span><b>__SIZE__</b><span>الحجم</span></div>
  <div class="qf"><span class="ic">🤖</span><b>7.0+</b><span>Android</span></div>
  <div class="qf"><span class="ic">🌐</span><b>الإنترنت</b><span>الأذونات</span></div>
  <div class="qf"><span class="ic">🏷️</span><b>Construtech</b><span>المطور</span></div>
</div>

<div class="hero-actions">
  <a class="dl-btn" id="dlBtn" href="../apks/__APK__" download>⬇ تحميل وتثبيت</a>
  <a class="pdf-btn" href="../guides/__KEY__-guide.pdf" download>📄 دليل الاستخدام (PDF)</a>
</div>
<p class="dl-hint">عند الضغط، يبدأ تحميل ملف APK — وبعدها تظهر خطوات التثبيت تلقائيًا في الأسفل 👇</p>

<div class="shots">
__SHOTS__
</div>

<main>
  <section>
    <h2>لماذا __NAME__</h2>
    <div class="highlights">
__HIGHLIGHTS__
    </div>
  </section>

  <section class="audience">
    <h2>الفئة المستهدفة</h2>
    <p>__AUDIENCE__</p>
  </section>

  <section>
    <h2>ما يقدّمه التطبيق</h2>
    <div class="chips">
__CHIPS__
    </div>
  </section>

  <section>
    <h2>كيف تبدأ باستخدامه</h2>
    <ol>
__USAGE__
    </ol>
  </section>

  <section>
    <h2>معلومات التطبيق</h2>
    <table class="infotable">
      <tr><td>الحجم</td><td>__SIZE__</td></tr>
      <tr><td>يتطلب</td><td>__MIN_ANDROID__</td></tr>
      <tr><td>الأذونات</td><td>__PERMISSIONS__</td></tr>
      <tr><td>المطوّر</td><td>Construtech</td></tr>
      <tr><td>النسخة الحالية</td><td>__VERSION__</td></tr>
    </table>
  </section>

  <section class="faq">
    <h2>أسئلة شائعة</h2>
__FAQ__
  </section>

  <section class="install-steps" id="installSteps">
    <h2>طريقة التثبيت (خارج المتجر)</h2>
    <ol>
      <li>حمّل ملف <b>APK</b> من الزر أعلاه.</li>
      <li>إذا ظهر تنبيه "التثبيت من مصادر غير معروفة" — توجّه إلى <b>الإعدادات</b> واسمح بذلك لمتصفحك (مرة واحدة فقط).</li>
      <li>عد إلى ملف الـ APK الذي حمّلته وافتحه، ثم اضغط <b>تثبيت</b>.</li>
      <li>بعد التثبيت، يمكنك إلغاء السماح بـ"مصادر غير معروفة" إن رغبت.</li>
    </ol>
    <div class="note">ملاحظة: هذا التطبيق غير متوفر على Google Play — فهو تحميل مباشر (APK). تأكد دائمًا من مصدر الملف قبل تثبيت أي تطبيق على هاتفك.__EXTRA_NOTE__</div>
    <div class="qr-box">
      <img src="../qrcodes/__KEY__.png" alt="رمز QR لتحميل __NAME__ مباشرة" loading="lazy">
      <div class="qt"><b>📷 امسح للتثبيت المباشر</b><span>صوّر الرمز بكاميرا هاتفك — يبدأ تحميل __NAME__ __VERSION__ فورًا.</span></div>
    </div>
  </section>
</main>

<footer>__NAME__ — Construtech © <span id="y"></span></footer>
<script>
  document.getElementById('y').textContent = new Date().getFullYear();
  (function(){
    var el = document.getElementById('updatedBadge');
    var d = el && el.getAttribute('data-updated');
    if(!d) return;
    var updated = new Date(d + 'T00:00:00');
    if(isNaN(updated.getTime())) return;
    var days = (Date.now() - updated.getTime()) / 86400000;
    if(days >= 0 && days <= 7) el.style.display = 'inline-flex';
  })();
  (function(){
    var dl = document.getElementById('dlBtn');
    var steps = document.getElementById('installSteps');
    if(!dl || !steps) return;
    dl.addEventListener('click', function(){
      setTimeout(function(){
        steps.scrollIntoView({behavior:'smooth', block:'start'});
        steps.classList.add('pulse');
        setTimeout(function(){ steps.classList.remove('pulse'); }, 3000);
      }, 450);
    });
  })();
</script>
</body>
</html>
'''


def render_qr_png(text, out_path, color_hex, module_px, logo_path):
    from PIL import Image, ImageDraw
    LIB = ctypes.CDLL("libqrencode.so.4")
    LIB.QRcode_encodeString.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]

    class QRcode(ctypes.Structure):
        _fields_ = [("version", ctypes.c_int), ("width", ctypes.c_int), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    LIB.QRcode_encodeString.restype = ctypes.POINTER(QRcode)
    LIB.QRcode_free.argtypes = [ctypes.POINTER(QRcode)]
    qr_ptr = LIB.QRcode_encodeString(text.encode("utf-8"), 6, 2, 2, 1)
    if not qr_ptr:
        raise RuntimeError("QR encode failed")
    qr = qr_ptr.contents
    w = qr.width
    buf = ctypes.cast(qr.data, ctypes.POINTER(ctypes.c_ubyte * (w * w))).contents
    matrix = [[bool(buf[y * w + x] & 1) for x in range(w)] for y in range(w)]
    LIB.QRcode_free(qr_ptr)

    n = len(matrix)
    border_modules = 4
    size = (n + border_modules * 2) * module_px
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    fg = tuple(int(color_hex.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
    off = border_modules * module_px
    for y in range(n):
        for x in range(n):
            if matrix[y][x]:
                x0, y0 = off + x * module_px, off + y * module_px
                draw.rounded_rectangle([x0, y0, x0 + module_px - 1, y0 + module_px - 1], radius=module_px // 4, fill=fg)
    if logo_path and os.path.isfile(logo_path):
        logo_size = size // 4
        pad = logo_size // 6
        logo = Image.open(logo_path).convert("RGBA").resize((logo_size, logo_size))
        canvas = Image.new("RGBA", (logo_size + pad * 2, logo_size + pad * 2), "white")
        mask = Image.new("L", canvas.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, canvas.size[0] - 1, canvas.size[1] - 1], radius=canvas.size[0] // 5, fill=255)
        canvas.paste(logo, (pad, pad), logo)
        img.paste(canvas, ((size - canvas.size[0]) // 2, (size - canvas.size[1]) // 2), mask=mask)
    img.save(out_path)


def export_one(key, dest_root, base_url):
    a = applications[key]
    pub = os.path.join(dest_root, "public")
    for sub in ("apps", "apks", "guides", "screenshots", "logos", "qrcodes"):
        os.makedirs(os.path.join(pub, sub), exist_ok=True)
    os.makedirs(os.path.join(pub, "screenshots", key), exist_ok=True)

    # 1) APK
    src_apk = os.path.join(REPO_ROOT, "apks", a["APK"])
    if not os.path.isfile(src_apk):
        raise SystemExit(f"missing source APK: {src_apk} (run update_app.py first)")
    dst_apk = os.path.join(pub, "apks", a["APK"])
    shutil.copy2(src_apk, dst_apk)

    # 2) logo
    src_logo = os.path.join(REPO_ROOT, "logos", a["LOGO"])
    if os.path.isfile(src_logo):
        shutil.copy2(src_logo, os.path.join(pub, "logos", a["LOGO"]))

    # 3) guide PDF
    src_guide = os.path.join(REPO_ROOT, "guides", f"{key}-guide.pdf")
    if os.path.isfile(src_guide):
        shutil.copy2(src_guide, os.path.join(pub, "guides", f"{key}-guide.pdf"))

    # 4) screenshots (only the ones actually used on the page)
    for s in a.get("SHOTS", []):
        src_s = os.path.join(REPO_ROOT, "screenshots", key, s)
        if os.path.isfile(src_s):
            shutil.copy2(src_s, os.path.join(pub, "screenshots", key, s))

    # 5) QR code, pointing at the titterisoft domain's own APK path
    url = f"{base_url}/apks/{a['APK']}"
    render_qr_png(url, os.path.join(pub, "qrcodes", f"{key}.png"),
                  color_hex=a["COLOR"]["primary"], module_px=10,
                  logo_path=os.path.join(pub, "logos", a["LOGO"]))

    # 6) the page itself
    updates_path = os.path.join(HERE, "updates.json")
    updated = ""
    if os.path.isfile(updates_path):
        import json
        updated = json.load(open(updates_path, encoding="utf-8")).get(key, "")

    html = TPL
    html = html.replace("__NAME__", a["NAME"])
    html = html.replace("__VERSION__", a["VERSION"])
    html = html.replace("__LOGO__", a["LOGO"])
    html = html.replace("__APK__", a["APK"])
    html = html.replace("__KEY__", key)
    html = html.replace("__TAGLINE__", a["TAGLINE"])
    html = html.replace("__AUDIENCE__", a["AUDIENCE"])
    html = html.replace("__UPDATED__", updated)
    html = html.replace("__MIN_ANDROID__", MIN_ANDROID)
    html = html.replace("__PERMISSIONS__", PERMISSIONS)
    html = html.replace("__SIZE__", human_size(dst_apk) or "—")

    chips = "\n".join(f'      <div class="chip">{c}</div>' for c in a["FEATURES"])
    html = html.replace("__CHIPS__", chips)
    usage = "\n".join(f"      <li>{u}</li>" for u in a["USAGE"])
    html = html.replace("__USAGE__", usage)
    hl = "\n".join(
        f'      <div class="hl-card"><span class="ic">{h["icon"]}</span><h3>{h["title"]}</h3><p>{h["desc"]}</p></div>'
        for h in a["HIGHLIGHTS"]
    )
    html = html.replace("__HIGHLIGHTS__", hl)

    faq_items = [
        ("هل هذا التطبيق آمن؟",
         "التطبيق غير متوفر على Google Play، وهو تحميل مباشر (APK) موقَّع من Construtech. تأكد دائمًا من أنك حمّلته من هذه الصفحة بالذات قبل تثبيته."),
    ]
    if a.get("LOCAL_DATA"):
        faq_items.append((
            "أين تُخزَّن بياناتي؟",
            "البيانات التي تُدخلها تُخزَّن محليًا في هاتفك داخل التطبيق — لا يوجد أي خادم خارجي يخزّن معطياتك.",
        ))
    faq_items.append((
        "كيف أعرف إذا صدر تحديث جديد؟",
        "عند صدور تحديث للتطبيق، تظهر ملاحظة خضراء تحت هذه الصفحة لمدة أسبوع. يمكنك دائمًا العودة إلى هنا لتحميل آخر نسخة.",
    ))
    faq_html = "\n".join(f'    <details><summary>{q}</summary><p>{ans}</p></details>' for q, ans in faq_items)
    html = html.replace("__FAQ__", faq_html)

    if a["SHOTS"]:
        imgs = "\n".join(f'    <img src="../screenshots/{key}/{s}" alt="لقطة من {a["NAME"]}" loading="lazy">' for s in a["SHOTS"])
        shots_html = f'  <div class="shots-row">\n{imgs}\n  </div>'
        extra_note = ""
    else:
        shots_html = '  <p class="shots-empty">تعذّر علينا عرض لقطات شاشة لهذا التطبيق — محتواه مخزَّن بصيغة لا يمكن قراءتها مباشرة من الخارج.</p>'
        extra_note = " لم نتمكن من عرض لقطات شاشة حقيقية لهذا التطبيق بالتحديد (راجع الملاحظة أعلاه)."
    html = html.replace("__SHOTS__", shots_html)
    html = html.replace("__EXTRA_NOTE__", extra_note)

    with open(os.path.join(pub, "apps", f"{key}.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"exported {key} -> {dest_root}/public/apps/{key}.html")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, help="path to a titterisoft-website checkout")
    ap.add_argument("--key", choices=list(applications.keys()), help="export only this app (default: all 5)")
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = ap.parse_args()

    keys = [args.key] if args.key else list(applications.keys())
    for key in keys:
        export_one(key, args.dest, args.base_url)


if __name__ == "__main__":
    main()

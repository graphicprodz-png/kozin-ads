"""Export one or all apps' full download-page system (page + APK + PDF guide +
screenshots + QR code) from kozin-ads into a titterisoft-website checkout.

The page itself is written as a *content fragment* to
<dest>/src/pages/apps/<key>.html, in titterisoft-website's own page format
(a leading JSON meta comment + body). titterisoft's Node build
(scripts/build.mjs) wraps it with the site's real, current header/nav/footer
and site-wide <head> — so the app page always matches the rest of the site
automatically, with zero duplicated header/footer markup here.

Everything else (APK, PDF guide, screenshots, logo, QR code) is copied into
<dest>/public/{apks,guides,screenshots,logos,qrcodes}/ as before, served
verbatim by Cloudflare Pages at the same relative paths the page links to
(../apks/<APK>, etc. — dist/apps/<key>.html sits at the same depth as
dist/apks/, dist/guides/, ... either way). The QR code is re-rendered to
point at the titterisoft domain instead of kozin-ads.

Usage:
  python3 export_to_titterisoft.py --dest /path/to/titterisoft-website [--key windoor] [--base-url https://tettrisoft.pages.dev]

Requires: the app's current apk/guide/screenshots already present under
kozin-ads's own apks/, guides/, screenshots/<key>/ (i.e. run update_app.py
first when syncing a single app after a fresh build).
"""
import argparse, ctypes, json, os, sys, shutil

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


# Body-only fragment: titterisoft-website's build wraps this with the site's
# real <head>/header/nav/footer (src/partials/layout.html), so it is always
# visually identical to the rest of the site — no header/footer duplicated
# here, no separate color/font system to keep in sync by hand.
TPL = '''<section class="dark page-hero app-hero">
  <div class="container">
    <nav class="crumbs" aria-label="مسار التصفح"><a href="/">الرئيسية</a><span aria-hidden="true">/</span><a href="/projects">مشاريعنا وتطبيقاتنا</a><span aria-hidden="true">/</span><span>__NAME__</span></nav>
    <span class="kicker kicker--line">__VERSION__ · Android · APK مباشر</span>
    <div class="app-hero__row">
      <img class="app-hero__icon" src="../logos/__LOGO__" alt="شعار __NAME__" width="88" height="88">
      <div>
        <h1>__NAME__</h1>
        <p>__TAGLINE__</p>
      </div>
    </div>
    <p class="app-updated" id="updatedBadge" data-updated="__UPDATED__">🆕 تم تحديث التطبيق مؤخرًا</p>
    <div class="app-hero__actions">
      <a class="btn btn--primary" id="dlBtn" href="../apks/__APK__" download>تحميل وتثبيت<svg class="icon" aria-hidden="true"><use href="#i-arrow"/></svg></a>
      <a class="btn btn--ghost" href="../guides/__KEY__-guide.pdf" download>دليل الاستخدام (PDF)</a>
    </div>
    <p class="app-hero__hint">عند الضغط يبدأ تحميل ملف APK — وتظهر خطوات التثبيت تلقائيًا أسفل الصفحة.</p>
  </div>
</section>

<section class="section section--tight">
  <div class="container app-quickfacts">
    <div class="app-qf"><svg class="icon" aria-hidden="true"><use href="#i-layers"/></svg><b>__SIZE__</b><span>الحجم</span></div>
    <div class="app-qf"><svg class="icon" aria-hidden="true"><use href="#i-phone"/></svg><b>7.0+</b><span>Android</span></div>
    <div class="app-qf"><svg class="icon" aria-hidden="true"><use href="#i-web"/></svg><b>الإنترنت</b><span>الأذونات</span></div>
    <div class="app-qf"><svg class="icon" aria-hidden="true"><use href="#i-award"/></svg><b>Construtech</b><span>المطوّر</span></div>
  </div>

  <div class="container app-shots">
__SHOTS__
  </div>
</section>

<section class="section section--alt">
  <div class="container">
    <header class="section__head section__head--start reveal">
      <span class="kicker">لماذا __NAME__</span>
    </header>
    <div class="app-highlights">
__HIGHLIGHTS__
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="container grid grid--2">
    <article class="card reveal">
      <h3>الفئة المستهدفة</h3>
      <p>__AUDIENCE__</p>
    </article>
    <article class="card reveal">
      <h3>ما يقدّمه التطبيق</h3>
      <div class="app-chips">
__CHIPS__
      </div>
    </article>
  </div>
</section>

<section class="section section--alt">
  <div class="container grid grid--2">
    <article class="card reveal app-install">
      <h3>كيف تبدأ باستخدامه</h3>
      <ol>
__USAGE__
      </ol>
    </article>
    <article class="card reveal">
      <h3>معلومات التطبيق</h3>
      <table class="app-table">
        <tr><td>الحجم</td><td>__SIZE__</td></tr>
        <tr><td>يتطلب</td><td>__MIN_ANDROID__</td></tr>
        <tr><td>الأذونات</td><td>__PERMISSIONS__</td></tr>
        <tr><td>المطوّر</td><td>Construtech</td></tr>
        <tr><td>النسخة الحالية</td><td>__VERSION__</td></tr>
      </table>
    </article>
  </div>
</section>

<section class="section section--tight">
  <div class="container grid grid--2">
    <article class="card reveal app-faq">
      <h3>أسئلة شائعة</h3>
__FAQ__
    </article>
    <article class="card reveal app-install">
      <h3>طريقة التثبيت (خارج المتجر)</h3>
      <ol>
        <li>حمّل ملف <b>APK</b> من الزر أعلاه.</li>
        <li>إذا ظهر تنبيه "التثبيت من مصادر غير معروفة" — توجّه إلى <b>الإعدادات</b> واسمح بذلك لمتصفحك (مرة واحدة فقط).</li>
        <li>عد إلى ملف الـ APK الذي حمّلته وافتحه، ثم اضغط <b>تثبيت</b>.</li>
        <li>بعد التثبيت، يمكنك إلغاء السماح بـ"مصادر غير معروفة" إن رغبت.</li>
      </ol>
      <div class="note">ملاحظة: هذا التطبيق غير متوفر على Google Play — فهو تحميل مباشر (APK). تأكد دائمًا من مصدر الملف قبل تثبيت أي تطبيق على هاتفك.__EXTRA_NOTE__</div>
      <div class="app-qr">
        <img src="../qrcodes/__KEY__.png" alt="رمز QR لتحميل __NAME__ مباشرة" loading="lazy">
        <div><b>📷 امسح للتثبيت المباشر</b><span>صوّر الرمز بكاميرا هاتفك — يبدأ تحميل __NAME__ __VERSION__ فورًا.</span></div>
      </div>
    </article>
  </div>
</section>

{{cta}}

<script>
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
  if(!dl) return;
  dl.addEventListener('click', function(){
    var steps = document.querySelector('.app-install');
    if(!steps) return;
    setTimeout(function(){ steps.scrollIntoView({behavior:'smooth', block:'start'}); }, 450);
  });
})();
</script>
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
    pages_dir = os.path.join(dest_root, "src", "pages", "apps")
    for sub in ("apks", "guides", "screenshots", "logos", "qrcodes"):
        os.makedirs(os.path.join(pub, sub), exist_ok=True)
    os.makedirs(os.path.join(pub, "screenshots", key), exist_ok=True)
    os.makedirs(pages_dir, exist_ok=True)

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

    # 6) the page content fragment
    updates_path = os.path.join(HERE, "updates.json")
    updated = ""
    if os.path.isfile(updates_path):
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

    chips = "\n".join(f'        <span class="chip">{c}</span>' for c in a["FEATURES"])
    html = html.replace("__CHIPS__", chips)
    usage = "\n".join(f"        <li>{u}</li>" for u in a["USAGE"])
    html = html.replace("__USAGE__", usage)
    hl = "\n".join(
        f'      <article class="card reveal"><div class="card__icon"><span aria-hidden="true" style="font-size:26px">{h["icon"]}</span></div><h3>{h["title"]}</h3><p>{h["desc"]}</p></article>'
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
        "عند صدور تحديث للتطبيق، تظهر ملاحظة خضراء أعلى هذه الصفحة لمدة أسبوع. يمكنك دائمًا العودة إلى هنا لتحميل آخر نسخة.",
    ))
    faq_html = "\n".join(f'      <details><summary>{q}</summary><p>{ans}</p></details>' for q, ans in faq_items)
    html = html.replace("__FAQ__", faq_html)

    if a["SHOTS"]:
        imgs = "\n".join(f'    <img src="../screenshots/{key}/{s}" alt="لقطة من {a["NAME"]}" loading="lazy">' for s in a["SHOTS"])
        shots_html = f'  <div class="app-shots__row">\n{imgs}\n  </div>'
        extra_note = ""
    else:
        shots_html = '  <p class="app-shots__empty">تعذّر علينا عرض لقطات شاشة لهذا التطبيق — محتواه مخزَّن بصيغة لا يمكن قراءتها مباشرة من الخارج.</p>'
        extra_note = " لم نتمكن من عرض لقطات شاشة حقيقية لهذا التطبيق بالتحديد (راجع الملاحظة أعلاه)."
    html = html.replace("__SHOTS__", shots_html)
    html = html.replace("__EXTRA_NOTE__", extra_note)

    meta = {
        "key": f"app-{key}",
        "title": f"{a['NAME']} {a['VERSION']} — تحميل وتعريف",
        "description": f"{a['NAME']} — {a['TAGLINE']}",
    }
    page = f"<!-- {json.dumps(meta, ensure_ascii=False)} -->\n{html}"

    with open(os.path.join(pages_dir, f"{key}.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print(f"exported {key} -> {dest_root}/src/pages/apps/{key}.html")

    # Clean up the old (pre-redesign) standalone page if still present from
    # an earlier export, so there's only ever one copy of each app page.
    old_page = os.path.join(pub, "apps", f"{key}.html")
    if os.path.isfile(old_page):
        os.remove(old_page)
        print(f"removed stale {old_page}")


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

# أدوات تحديث الموقع (kozin-ads)

هاذ المجلد فيه السكريبتات اللي كيبنيو الموقع (صفحات التطبيقات، الصفحة الرئيسية، دلائل PDF) من مصدر وحيد: `app_data.py`.

## تحديث يدوي لتطبيق واحد

```bash
pip install --break-system-packages playwright
playwright install --with-deps chromium

python3 tools/update_app.py --key windoor --version v2.55 --apk /path/to/Windoor.apk
```

هاذ الأمر كيدير:
1. يبدل ملف الـ APK فـ `apks/`
2. يحدث الرقم فـ `tools/app_data.py`
3. يحدث الكارطة فـ `index.html`
4. يعاود يبني صفحة التطبيق (`apps/<key>.html`)
5. يعاود يبني دليل الاستخدام (`guides/<key>-guide.pdf`)

من بعد، دير commit + push بروحك.

## إعادة بناء كلشي

```bash
python3 tools/build_apps.py        # كل صفحات apps/*.html
python3 tools/build_guides.py      # كل ملفات guides/*.pdf
```

## التحديث الأوتوماتيكي (GitHub Action)

ريبو `kitchen-calc` فيه workflow (`.github/workflows/sync-kozin-ads.yml`) كيتشغل أوتوماتيكيا كل مرة يتنشر release جديد بإسم (tag) من هاذو: `latest` (Kozinalum), `windoor`, `rclean`, `plafonpro`, `windoorgulf`.

كيدير نفس خطوات `update_app.py` فوق، وكيعمل push مباشرة لريبو `kozin-ads`.

**شرط واحد يدوي:** لازم يكون عندو secret إسمو `KOZIN_ADS_TOKEN` فإعدادات ريبو `kitchen-calc` (Settings → Secrets and variables → Actions) — Personal Access Token عندو صلاحية الكتابة (`repo`) فريبو `kozin-ads`. هاذ التوكن خاص المستخدم يصاوبها بروحو من GitHub (Settings → Developer settings → Personal access tokens) وما يبعتهاش فالشات.

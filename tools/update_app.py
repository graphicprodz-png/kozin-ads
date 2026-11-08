"""Update one app's version + APK across the whole kozin-ads site: app_data.py,
index.html card, the app's own page, and its PDF guide.

Usage:
  python3 update_app.py --key windoor --version v2.55 --apk /path/to/Windoor.apk

Requires (for the regen steps): pip install playwright && playwright install chromium
"""
import argparse, datetime, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, '..'))
UPDATES_PATH = os.path.join(HERE, 'updates.json')
sys.path.insert(0, HERE)
from app_data import applications  # noqa: E402

def mark_updated_today(key):
    data = {}
    if os.path.isfile(UPDATES_PATH):
        data = json.load(open(UPDATES_PATH, encoding='utf-8'))
    today = datetime.date.today().isoformat()
    data[key] = today
    json.dump(data, open(UPDATES_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f"updates.json: {key} -> {today}")
    return today

def update_app_data_version(key, new_version):
    path = os.path.join(HERE, 'app_data.py')
    src = open(path, encoding='utf-8').read()
    # Find this key's dict( block, then replace its VERSION="..." field wherever it sits
    # inside it - some entries put DEV= (or other fields) between NAME= and VERSION=, so we
    # don't assume they're adjacent. Limited to a short window after the opening paren since
    # VERSION is always declared near the top, before any nested dict(...) (e.g. COLOR=dict(...))
    # that would otherwise make bracket-matching this block non-trivial.
    start = re.search(r'"' + re.escape(key) + r'":\s*dict\(', src)
    if not start:
        raise SystemExit(f"could not find dict( block for key={key} in app_data.py")
    window_end = min(len(src), start.end() + 400)
    window = src[start.end():window_end]
    new_window, n = re.subn(r'VERSION="[^"]*"', f'VERSION="{new_version}"', window, count=1)
    if n != 1:
        raise SystemExit(f"could not find/replace VERSION for key={key} in app_data.py (matched {n} times)")
    new_src = src[:start.end()] + new_window + src[window_end:]
    open(path, 'w', encoding='utf-8').write(new_src)
    print(f"app_data.py: {key} -> VERSION={new_version}")

def update_index_html(key, new_version, updated_date=None):
    path = os.path.join(REPO_ROOT, 'index.html')
    src = open(path, encoding='utf-8').read()
    # Match the whole object literal line for this app (identified by its page path) and
    # replace only its version:"..." (and, if given, updated:"...") fields.
    pattern = re.compile(
        r'(\{[^{}]*page:"apps/' + re.escape(key) + r'\.html"[^{}]*\})'
    )
    m = pattern.search(src)
    if not m:
        # Not every app is listed on the public landing page (e.g. Windoor is only
        # distributed directly, not via a kozin-ads card) - that's a deliberate choice, not
        # a bug, so don't fail the whole sync over it.
        print(f"index.html: no public card for key={key} - skipping (not listed on landing page)")
        return
    entry = m.group(1)
    new_entry, n = re.subn(r'version:"[^"]*"', f'version:"{new_version}"', entry, count=1)
    if n != 1:
        raise SystemExit(f"could not replace version field in index.html entry for key={key}")
    if updated_date:
        if re.search(r'updated:"[^"]*"', new_entry):
            new_entry = re.sub(r'updated:"[^"]*"', f'updated:"{updated_date}"', new_entry, count=1)
        else:
            new_entry = new_entry[:-1].rstrip(', ') + f', updated:"{updated_date}"}}'
    new_src = src[:m.start(1)] + new_entry + src[m.end(1):]
    open(path, 'w', encoding='utf-8').write(new_src)
    print(f"index.html: {key} card -> version:\"{new_version}\"")

def copy_apk(key, apk_src_path):
    a = applications[key]
    dest = os.path.join(REPO_ROOT, 'apks', a['APK'])
    shutil.copy2(apk_src_path, dest)
    print(f"apks/{a['APK']} updated ({os.path.getsize(dest)} bytes)")

def regen_page(key):
    subprocess.run([sys.executable, os.path.join(HERE, 'build_apps.py'), key], check=True)

def regen_guide(key):
    subprocess.run([sys.executable, os.path.join(HERE, 'build_guides.py'), key], check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--key', required=True, choices=list(applications.keys()))
    ap.add_argument('--version', required=True, help='e.g. v2.55')
    ap.add_argument('--apk', required=True, help='path to the new APK file')
    ap.add_argument('--skip-guide', action='store_true', help='skip PDF regeneration (faster, for testing)')
    args = ap.parse_args()

    if not os.path.isfile(args.apk):
        raise SystemExit(f"APK not found: {args.apk}")

    old_version = applications[args.key]['VERSION']
    version_changed = old_version != args.version

    copy_apk(args.key, args.apk)
    update_app_data_version(args.key, args.version)
    if version_changed:
        today = mark_updated_today(args.key)
        update_index_html(args.key, args.version, updated_date=today)
    else:
        print(f"version unchanged ({old_version}) -> not touching updates.json")
        update_index_html(args.key, args.version)
    regen_page(args.key)
    if not args.skip_guide:
        regen_guide(args.key)
    print("done:", args.key, "->", args.version)

if __name__ == '__main__':
    main()

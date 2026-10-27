"""Update one app's version + APK across the whole kozin-ads site: app_data.py,
index.html card, the app's own page, and its PDF guide.

Usage:
  python3 update_app.py --key windoor --version v2.55 --apk /path/to/Windoor.apk

Requires (for the regen steps): pip install playwright && playwright install chromium
"""
import argparse, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from app_data import applications  # noqa: E402

def update_app_data_version(key, new_version):
    path = os.path.join(HERE, 'app_data.py')
    src = open(path, encoding='utf-8').read()
    # Find the dict block for this key: `"key": dict(\n ... VERSION="vX.Y", ...)`
    pattern = re.compile(
        r'("' + re.escape(key) + r'":\s*dict\(\s*\n\s*NAME="[^"]*",\s*VERSION=")([^"]*)(")'
    )
    new_src, n = pattern.subn(lambda m: m.group(1) + new_version + m.group(3), src)
    if n != 1:
        raise SystemExit(f"could not find/replace VERSION for key={key} in app_data.py (matched {n} times)")
    open(path, 'w', encoding='utf-8').write(new_src)
    print(f"app_data.py: {key} -> VERSION={new_version}")

def update_index_html(key, new_version):
    path = os.path.join(REPO_ROOT, 'index.html')
    src = open(path, encoding='utf-8').read()
    # Match the whole object literal line for this app (identified by its page path) and
    # replace only its version:"..." field.
    pattern = re.compile(
        r'(\{[^{}]*page:"apps/' + re.escape(key) + r'\.html"[^{}]*\})'
    )
    m = pattern.search(src)
    if not m:
        raise SystemExit(f"could not find index.html card entry for key={key}")
    entry = m.group(1)
    new_entry, n = re.subn(r'version:"[^"]*"', f'version:"{new_version}"', entry, count=1)
    if n != 1:
        raise SystemExit(f"could not replace version field in index.html entry for key={key}")
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

    copy_apk(args.key, args.apk)
    update_app_data_version(args.key, args.version)
    update_index_html(args.key, args.version)
    regen_page(args.key)
    if not args.skip_guide:
        regen_guide(args.key)
    print("done:", args.key, "->", args.version)

if __name__ == '__main__':
    main()

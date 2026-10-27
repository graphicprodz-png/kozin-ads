#!/usr/bin/env python3
"""Generate QR code PNGs using the system libqrencode4 via ctypes (no network
needed, no pip package). Produces a clean, branded QR (dark module color =
app accent, rounded white canvas) for each app's real APK direct-download URL.
"""
import ctypes, os, sys
from PIL import Image, ImageDraw

LIB = ctypes.CDLL("libqrencode.so.4")

# QRcode_encodeString(string, version, level, hint, casesensitive) -> QRcode*
LIB.QRcode_encodeString.restype = ctypes.c_void_p
LIB.QRcode_encodeString.argtypes = [
    ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int
]

class QRcode(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_int),
        ("width", ctypes.c_int),
        ("data", ctypes.POINTER(ctypes.c_ubyte)),
    ]

QR_ECLEVEL_Q = 2  # ~25% error correction, good for print
QR_MODE_8 = 2

def encode_matrix(text):
    LIB.QRcode_encodeString.restype = ctypes.POINTER(QRcode)
    qr_ptr = LIB.QRcode_encodeString(text.encode("utf-8"), 0, QR_ECLEVEL_Q, QR_MODE_8, 1)
    if not qr_ptr:
        raise RuntimeError("QR encode failed")
    qr = qr_ptr.contents
    w = qr.width
    buf = ctypes.cast(qr.data, ctypes.POINTER(ctypes.c_ubyte * (w * w))).contents
    matrix = [[bool(buf[y * w + x] & 1) for x in range(w)] for y in range(w)]
    LIB.QRcode_free(qr_ptr)
    return matrix

LIB.QRcode_free.argtypes = [ctypes.POINTER(QRcode)]

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def render_qr_png(text, out_path, color_hex="#1a1a1a", module_px=10, border_modules=4, logo_path=None):
    matrix = encode_matrix(text)
    n = len(matrix)
    size = (n + border_modules * 2) * module_px
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    fg = hex_to_rgb(color_hex)
    off = border_modules * module_px
    for y in range(n):
        for x in range(n):
            if matrix[y][x]:
                x0 = off + x * module_px
                y0 = off + y * module_px
                draw.rounded_rectangle([x0, y0, x0 + module_px - 1, y0 + module_px - 1], radius=module_px // 4, fill=fg)
    if logo_path and os.path.isfile(logo_path):
        logo_size = size // 4
        pad = logo_size // 6
        logo = Image.open(logo_path).convert("RGBA").resize((logo_size, logo_size))
        canvas = Image.new("RGBA", (logo_size + pad * 2, logo_size + pad * 2), "white")
        mask = Image.new("L", canvas.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, canvas.size[0]-1, canvas.size[1]-1], radius=canvas.size[0]//5, fill=255)
        canvas.paste(logo, (pad, pad), logo)
        img.paste(canvas, ((size - canvas.size[0]) // 2, (size - canvas.size[1]) // 2), mask=mask.resize(canvas.size) if mask.size != canvas.size else mask)
        # simpler: just overlay rounded white badge + logo using mask as alpha
    img.save(out_path)

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))
    from app_data import applications
    REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    BASE_URL = "https://graphicprodz-png.github.io/kozin-ads"
    out_dir = os.path.join(REPO_ROOT, "qrcodes")
    os.makedirs(out_dir, exist_ok=True)
    for key, a in applications.items():
        url = f"{BASE_URL}/apks/{a['APK']}"
        out_path = os.path.join(out_dir, f"{key}.png")
        logo_path = os.path.join(REPO_ROOT, "logos", a["LOGO"])
        render_qr_png(url, out_path, color_hex=a["COLOR"]["primary"], module_px=10, logo_path=logo_path)
        print(f"{key}: {url} -> {out_path}")

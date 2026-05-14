"""Génère les icônes PWA / manifeste (Chrome, écran d’accueil, base d’un build APK/TWA).

Usage :
    python scripts/generate_pwa_icons.py

Les icônes sont **100 % opaques** (fond crème #FFFCF8) : iOS affiche souvent le PNG
transparent comme carré noir sur l’écran d’accueil.

Source prioritaire :
    `static/images/icons/LOGO KWALOKWAKOLÈ GROUP.png`
Le noir **connecté aux bords** de l’image est remplacé par le fond crème (le texte
noir enfermé dans les glyphes reste intact si le fichier l’utilise).

Repli si fichier absent : composition générée sur fond crème.

Le favicon utilise `static/images/logo-kwalokwakole.png` (logo header).
"""
from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "static" / "images" / "icons"
LAUNCHER_SRC = OUT_DIR / "LOGO KWALOKWAKOLÈ GROUP.png"
SRC_LOGO_SITE = ROOT / "static" / "images" / "logo-kwalokwakole.png"

# Aligné sur manifest.webmanifest background_color
ICON_BG = (255, 252, 248)

PRIMARY = (194, 65, 12, 255)
INK = (27, 20, 16, 255)
MUTED = (107, 95, 84, 255)


def _edge_flood_replace_dark(
    img: Image.Image,
    darkness: int = 52,
    repl: tuple[int, int, int] = ICON_BG,
) -> Image.Image:
    """Remplace les pixels très sombres reliés au bord (fond) par `repl`."""
    im = img.convert("RGBA")
    w, h = im.size
    px = im.load()
    n = w * h
    vis = bytearray(n)

    def dark(x: int, y: int) -> bool:
        r, g, b, a = px[x, y]
        return a > 35 and r <= darkness and g <= darkness and b <= darkness

    def idx(x: int, y: int) -> int:
        return y * w + x

    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        for yy in (0, h - 1):
            if dark(x, yy) and not vis[idx(x, yy)]:
                vis[idx(x, yy)] = 1
                q.append((x, yy))
    for y in range(h):
        for xx in (0, w - 1):
            if dark(xx, y) and not vis[idx(xx, y)]:
                vis[idx(xx, y)] = 1
                q.append((xx, y))

    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not vis[idx(nx, ny)] and dark(nx, ny):
                vis[idx(nx, ny)] = 1
                q.append((nx, ny))

    out = im.copy()
    op = out.load()
    rr, gg, bb = repl
    for y in range(h):
        row = y * w
        for x in range(w):
            if vis[row + x]:
                op[x, y] = (rr, gg, bb, 255)
    return out


def _icon_on_opaque(
    src: Image.Image,
    size: int,
    margin_ratio: float,
    bg_rgb: tuple[int, int, int] = ICON_BG,
) -> Image.Image:
    w, h = src.size
    inner = max(1, int(size * (1 - 2 * margin_ratio)))
    ratio = min(inner / w, inner / h)
    new_w, new_h = max(1, int(w * ratio)), max(1, int(h * ratio))
    resized = src.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (*bg_rgb, 255))
    canvas.paste(resized, ((size - new_w) // 2, (size - new_h) // 2), resized)
    return canvas.convert("RGB")


def _opaque_favicon(src: Image.Image, size: int, bg_rgb: tuple[int, int, int] = ICON_BG) -> Image.Image:
    w, h = src.size
    ratio = min(size / w, size / h)
    new_w, new_h = max(1, int(w * ratio)), max(1, int(h * ratio))
    resized = src.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (*bg_rgb, 255))
    canvas.paste(resized, ((size - new_w) // 2, (size - new_h) // 2), resized)
    return canvas.convert("RGB")


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size = max(8, int(size))
    candidates = [
        Path(r"C:\Windows\Fonts\segoeuib.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _draw_fallback_launcher(size: int, margin_ratio: float) -> Image.Image:
    """Repli si le PNG source n’existe pas — fond crème opaque."""
    img = Image.new("RGBA", (size, size), (*ICON_BG, 255))
    draw = ImageDraw.Draw(img)
    m = max(2, int(size * margin_ratio))
    usable = size - 2 * m
    sq = max(18, int(usable * 0.28))
    x0 = m
    y0 = m + (usable - sq) // 2
    r = max(3, int(sq * 0.14))
    draw.rounded_rectangle([x0, y0, x0 + sq, y0 + sq], radius=r, fill=PRIMARY)
    font_k = _load_font(int(sq * 0.5))
    kb = draw.textbbox((0, 0), "K", font=font_k)
    kw, kh = kb[2] - kb[0], kb[3] - kb[1]
    draw.text(
        (x0 + (sq - kw) // 2 - kb[0], y0 + (sq - kh) // 2 - kb[1]),
        "K",
        font=font_k,
        fill=(255, 255, 255, 255),
    )
    tx = x0 + sq + max(4, int(usable * 0.04))
    font_main = _load_font(max(11, int(size * 0.068)))
    font_sub = _load_font(max(8, int(size * 0.036)))
    main_text = "Kolêgroup"
    sub_text = "GROUP"
    y_main = y0 + max(0, int(sq * 0.08))
    main_bbox = draw.textbbox((tx, y_main), main_text, font=font_main)
    if main_bbox[2] > size - m - 2:
        font_main = _load_font(max(9, int(size * 0.052)))
        main_bbox = draw.textbbox((tx, y_main), main_text, font=font_main)
    draw.text((tx, y_main), main_text, font=font_main, fill=INK)
    sb = draw.textbbox((0, 0), sub_text, font=font_sub)
    sw = sb[2] - sb[0]
    sx = main_bbox[2] - sw
    sy = main_bbox[3] + max(1, int(size * 0.014))
    draw.text((sx, sy), sub_text, font=font_sub, fill=MUTED)
    return img


def _prepare_launcher_source() -> Image.Image:
    if LAUNCHER_SRC.is_file():
        raw = Image.open(LAUNCHER_SRC).convert("RGBA")
        return _edge_flood_replace_dark(raw)
    return _draw_fallback_launcher(512, 0.08)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if LAUNCHER_SRC.is_file():
        src = _prepare_launcher_source()
    else:
        print("Avertissement :", LAUNCHER_SRC.name, "introuvable — icône de repli.")
        src = _draw_fallback_launcher(512, 0.08)

    _icon_on_opaque(src, 192, margin_ratio=0.08).save(OUT_DIR / "icon-192.png", "PNG")
    _icon_on_opaque(src, 512, margin_ratio=0.08).save(OUT_DIR / "icon-512.png", "PNG")
    _icon_on_opaque(src, 512, margin_ratio=0.18).save(OUT_DIR / "icon-maskable-512.png", "PNG")
    _icon_on_opaque(src, 180, margin_ratio=0.08).save(OUT_DIR / "apple-touch-icon.png", "PNG")

    site_logo = Image.open(SRC_LOGO_SITE).convert("RGBA")
    _opaque_favicon(site_logo, 32).save(OUT_DIR / "favicon-32.png", "PNG")

    print("Icônes PWA (fond opaque) depuis", LAUNCHER_SRC.name if LAUNCHER_SRC.is_file() else "(repli)")
    print("Sortie :", OUT_DIR)


if __name__ == "__main__":
    main()

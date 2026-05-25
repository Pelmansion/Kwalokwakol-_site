"""Génère les icônes PWA / manifeste (Chrome, écran d’accueil, base d’un build APK/TWA).

Usage :
    python scripts/generate_pwa_icons.py

Source unique :
    `static/images/logo-kwalokwakole.png`

Fond : **dégradé chaud** (orange terracotta → brun profond), opaque — plus lisible
sur iOS qu’un PNG transparent et plus marqué qu’un fond blanc plat.

Les bords très **clairs** reliés au contour (fond blanc / gris clair du fichier) sont
passés en transparence avant composition sur le dégradé.

Repli si fichier absent : composition « K + Kolê Group » sur le même dégradé.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "static" / "images" / "icons"
SRC_LOGO = ROOT / "static" / "images" / "logo-kwalokwakole.png"

PRIMARY = (194, 65, 12, 255)


def _warm_launcher_gradient(size: int) -> Image.Image:
    """Dégradé diagonal orange vif → terracotta → brun (redimensionné proprement)."""
    w = h = 256
    img = Image.new("RGB", (w, h))
    px = img.load()
    # Coins : chaleur en haut-gauche, profondeur en bas-droite
    c0 = (251, 146, 60)  # orange clair
    c1 = (194, 65, 12)  # theme #C2410C
    c2 = (67, 32, 18)  # brun rouille
    c3 = (22, 12, 9)  # presque noir chaud
    for y in range(h):
        for x in range(w):
            t = (x / (w - 1) + y / (h - 1)) * 0.5  # 0 .. 1
            if t < 1 / 3:
                u = t * 3
                r = int(c0[0] + (c1[0] - c0[0]) * u)
                g = int(c0[1] + (c1[1] - c0[1]) * u)
                b = int(c0[2] + (c1[2] - c0[2]) * u)
            elif t < 2 / 3:
                u = (t - 1 / 3) * 3
                r = int(c1[0] + (c2[0] - c1[0]) * u)
                g = int(c1[1] + (c2[1] - c1[1]) * u)
                b = int(c1[2] + (c2[2] - c1[2]) * u)
            else:
                u = (t - 2 / 3) * 3
                r = int(c2[0] + (c3[0] - c2[0]) * u)
                g = int(c2[1] + (c3[1] - c2[1]) * u)
                b = int(c2[2] + (c3[2] - c2[2]) * u)
            px[x, y] = (r, g, b)
    return img.resize((size, size), Image.LANCZOS)


def _edge_flood_replace_light(img: Image.Image, lightness: int = 245) -> Image.Image:
    """Pixels très clairs reliés au bord → transparent (fond blanc autour du logo)."""
    im = img.convert("RGBA")
    w, h = im.size
    px = im.load()
    n = w * h
    vis = bytearray(n)

    def is_light(x: int, y: int) -> bool:
        r, g, b, a = px[x, y]
        return a > 30 and r >= lightness and g >= lightness and b >= lightness

    def idx(x: int, y: int) -> int:
        return y * w + x

    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        for yy in (0, h - 1):
            if is_light(x, yy) and not vis[idx(x, yy)]:
                vis[idx(x, yy)] = 1
                q.append((x, yy))
    for y in range(h):
        for xx in (0, w - 1):
            if is_light(xx, y) and not vis[idx(xx, y)]:
                vis[idx(xx, y)] = 1
                q.append((xx, y))

    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not vis[idx(nx, ny)] and is_light(nx, ny):
                vis[idx(nx, ny)] = 1
                q.append((nx, ny))

    out = im.copy()
    op = out.load()
    for y in range(h):
        row = y * w
        for x in range(w):
            if vis[row + x]:
                op[x, y] = (0, 0, 0, 0)
    return out


def _edge_flood_replace_dark(
    img: Image.Image,
    darkness: int = 52,
    repl: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> Image.Image:
    """Pixels très sombres reliés au bord → transparent (fond noir autour du logo)."""
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
    rr, gg, bb, aa = repl
    for y in range(h):
        row = y * w
        for x in range(w):
            if vis[row + x]:
                op[x, y] = (rr, gg, bb, aa)
    return out


def _prepare_logo_rgba() -> Image.Image:
    raw = Image.open(SRC_LOGO).convert("RGBA")
    w, h = raw.size
    max_side = 800
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        raw = raw.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    step = _edge_flood_replace_light(raw, lightness=246)
    step = _edge_flood_replace_dark(step, darkness=40, repl=(0, 0, 0, 0))
    return step


def _icon_on_gradient(
    src: Image.Image,
    size: int,
    margin_ratio: float,
    gradient: Image.Image,
) -> Image.Image:
    w, h = src.size
    inner = max(1, int(size * (1 - 2 * margin_ratio)))
    ratio = min(inner / w, inner / h)
    new_w, new_h = max(1, int(w * ratio)), max(1, int(h * ratio))
    resized = src.resize((new_w, new_h), Image.LANCZOS)
    canvas = gradient.resize((size, size), Image.LANCZOS).convert("RGBA")
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


def _draw_fallback_on_gradient(size: int, margin_ratio: float, gradient: Image.Image) -> Image.Image:
    """Repli vectoriel sur le dégradé."""
    base = gradient.resize((size, size), Image.LANCZOS).convert("RGBA")
    img = Image.new("RGBA", (size, size))
    img.paste(base, (0, 0))
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
    main_text = "Kolê Group"
    sub_text = ""
    y_main = y0 + max(0, int(sq * 0.08))
    main_bbox = draw.textbbox((tx, y_main), main_text, font=font_main)
    if main_bbox[2] > size - m - 2:
        font_main = _load_font(max(9, int(size * 0.052)))
        main_bbox = draw.textbbox((tx, y_main), main_text, font=font_main)
    draw.text((tx, y_main), main_text, font=font_main, fill=(255, 248, 241, 255))
    if sub_text:
        sb = draw.textbbox((0, 0), sub_text, font=font_sub)
        sw = sb[2] - sb[0]
        sx = main_bbox[2] - sw
        sy = main_bbox[3] + max(1, int(size * 0.014))
        draw.text((sx, sy), sub_text, font=font_sub, fill=(255, 220, 200, 230))
    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    g192 = _warm_launcher_gradient(192)
    g512 = _warm_launcher_gradient(512)
    g180 = _warm_launcher_gradient(180)
    g32 = _warm_launcher_gradient(32)

    if SRC_LOGO.is_file():
        src = _prepare_logo_rgba()
        _icon_on_gradient(src, 192, 0.08, g192).save(OUT_DIR / "icon-192.png", "PNG")
        _icon_on_gradient(src, 512, 0.08, g512).save(OUT_DIR / "icon-512.png", "PNG")
        _icon_on_gradient(src, 512, 0.18, g512).save(OUT_DIR / "icon-maskable-512.png", "PNG")
        _icon_on_gradient(src, 180, 0.08, g180).save(OUT_DIR / "apple-touch-icon.png", "PNG")
        _icon_on_gradient(src, 32, 0.06, g32).save(OUT_DIR / "favicon-32.png", "PNG")
        print("Icônes PWA générées depuis", SRC_LOGO.name, "(fond dégradé chaud)")
    else:
        print("Avertissement :", SRC_LOGO.name, "introuvable — repli vectoriel.")
        fb = _draw_fallback_on_gradient(512, 0.08, g512)
        _icon_on_gradient(fb, 192, 0.08, g192).save(OUT_DIR / "icon-192.png", "PNG")
        _icon_on_gradient(fb, 512, 0.08, g512).save(OUT_DIR / "icon-512.png", "PNG")
        _icon_on_gradient(fb, 512, 0.18, g512).save(OUT_DIR / "icon-maskable-512.png", "PNG")
        _icon_on_gradient(fb, 180, 0.08, g180).save(OUT_DIR / "apple-touch-icon.png", "PNG")
        _icon_on_gradient(fb, 32, 0.06, g32).save(OUT_DIR / "favicon-32.png", "PNG")

    print("Sortie :", OUT_DIR)


if __name__ == "__main__":
    main()

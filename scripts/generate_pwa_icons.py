"""Génère les icônes PWA / manifeste (Chrome, écran d’accueil, base d’un build APK/TWA).

Usage :
    python scripts/generate_pwa_icons.py

Source **icônes launcher** (prioritaire) :
    `static/images/icons/LOGO KWALOKWAKOLÈ GROUP.png`
    (fond noir retiré → transparence, puis redimensionnement sur carré transparent).

Si ce fichier est absent, repli : composition générée (K + Kolêgroup + GROUP).

Le **favicon** utilise toujours `static/images/logo-kwalokwakole.png` (logo site header).

**APK** : régénérez le paquet PWABuilder/Bubblewrap après déploiement pour embarquer les nouveaux PNG.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "static" / "images" / "icons"
LAUNCHER_SRC = OUT_DIR / "LOGO KWALOKWAKOLÈ GROUP.png"
SRC_LOGO_SITE = ROOT / "static" / "images" / "logo-kwalokwakole.png"

PRIMARY = (194, 65, 12, 255)
INK = (27, 20, 16, 255)
MUTED = (107, 95, 84, 255)


def _black_background_to_transparent(img: Image.Image, threshold: int = 42) -> Image.Image:
    """Pixels très sombres (fond noir) → alpha 0. Garde le marron du carré K et le blanc du texte."""
    rgba = img.convert("RGBA")
    pixels = list(rgba.getdata())
    out = []
    for r, g, b, a in pixels:
        if r <= threshold and g <= threshold and b <= threshold:
            out.append((0, 0, 0, 0))
        else:
            out.append((r, g, b, a))
    rgba.putdata(out)
    return rgba


def _icon_on_transparent(src: Image.Image, size: int, margin_ratio: float) -> Image.Image:
    w, h = src.size
    inner = max(1, int(size * (1 - 2 * margin_ratio)))
    ratio = min(inner / w, inner / h)
    new_w, new_h = max(1, int(w * ratio)), max(1, int(h * ratio))
    resized = src.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(resized, ((size - new_w) // 2, (size - new_h) // 2), resized)
    return canvas


def _transparent_favicon(src: Image.Image, size: int) -> Image.Image:
    w, h = src.size
    ratio = min(size / w, size / h)
    new_w, new_h = max(1, int(w * ratio)), max(1, int(h * ratio))
    resized = src.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(resized, ((size - new_w) // 2, (size - new_h) // 2), resized)
    return canvas


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
    """Repli si le PNG source n’existe pas."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
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


def _load_launcher_rgba() -> Image.Image:
    if LAUNCHER_SRC.is_file():
        raw = Image.open(LAUNCHER_SRC).convert("RGBA")
        return _black_background_to_transparent(raw)
    return _draw_fallback_launcher(512, 0.08)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if LAUNCHER_SRC.is_file():
        src = _load_launcher_rgba()
    else:
        print("Avertissement :", LAUNCHER_SRC.name, "introuvable — icône de repli vectorielle.")
        src = _draw_fallback_launcher(512, 0.08)

    _icon_on_transparent(src, 192, margin_ratio=0.08).save(OUT_DIR / "icon-192.png", "PNG")
    _icon_on_transparent(src, 512, margin_ratio=0.08).save(OUT_DIR / "icon-512.png", "PNG")
    _icon_on_transparent(src, 512, margin_ratio=0.18).save(OUT_DIR / "icon-maskable-512.png", "PNG")
    _icon_on_transparent(src, 180, margin_ratio=0.08).save(OUT_DIR / "apple-touch-icon.png", "PNG")

    site_logo = Image.open(SRC_LOGO_SITE).convert("RGBA")
    _transparent_favicon(site_logo, 32).save(OUT_DIR / "favicon-32.png", "PNG")

    print("Icônes PWA générées depuis", LAUNCHER_SRC.name if LAUNCHER_SRC.is_file() else "(repli)")
    print("Sortie :", OUT_DIR)


if __name__ == "__main__":
    main()

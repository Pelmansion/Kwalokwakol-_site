"""Génère les icônes PWA à partir du logo principal.

Usage :
    python scripts/generate_pwa_icons.py

Le script lit une image source PNG (ex. `static/images/logo-kwalokwakole.png` exportée depuis le wordmark SVG) et produit :
  - static/images/icons/icon-192.png
  - static/images/icons/icon-512.png
  - static/images/icons/icon-maskable-512.png (zone de sécurité 20 %)
  - static/images/icons/apple-touch-icon.png (180x180)
  - static/images/icons/favicon-32.png
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "static" / "images" / "logo-kwalokwakole.png"
OUT_DIR = ROOT / "static" / "images" / "icons"
BRAND_BG = (194, 65, 12)  # #C2410C (primary theme color)


def _load_rgba() -> Image.Image:
    img = Image.open(SRC).convert("RGBA")
    return img


def _fit_on_square(src: Image.Image, size: int, bg: tuple[int, int, int], margin_ratio: float = 0.12) -> Image.Image:
    """Place l'image source centrée sur un carré coloré."""
    canvas = Image.new("RGB", (size, size), bg)
    inner = int(size * (1 - 2 * margin_ratio))
    w, h = src.size
    ratio = min(inner / w, inner / h)
    new_w, new_h = int(w * ratio), int(h * ratio)
    resized = src.resize((new_w, new_h), Image.LANCZOS)
    offset = ((size - new_w) // 2, (size - new_h) // 2)
    canvas.paste(resized, offset, resized if resized.mode == "RGBA" else None)
    return canvas


def _transparent(src: Image.Image, size: int) -> Image.Image:
    """Redimensionne le logo en gardant la transparence."""
    w, h = src.size
    ratio = min(size / w, size / h)
    new_w, new_h = int(w * ratio), int(h * ratio)
    resized = src.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    canvas.paste(resized, ((size - new_w) // 2, (size - new_h) // 2), resized)
    return canvas


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    logo = _load_rgba()

    _fit_on_square(logo, 192, BRAND_BG, margin_ratio=0.10).save(OUT_DIR / "icon-192.png", "PNG")
    _fit_on_square(logo, 512, BRAND_BG, margin_ratio=0.10).save(OUT_DIR / "icon-512.png", "PNG")
    _fit_on_square(logo, 512, BRAND_BG, margin_ratio=0.22).save(OUT_DIR / "icon-maskable-512.png", "PNG")
    _fit_on_square(logo, 180, BRAND_BG, margin_ratio=0.10).save(OUT_DIR / "apple-touch-icon.png", "PNG")
    _transparent(logo, 32).save(OUT_DIR / "favicon-32.png", "PNG")

    print("Icônes PWA générées dans", OUT_DIR)


if __name__ == "__main__":
    main()

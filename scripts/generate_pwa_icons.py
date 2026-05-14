"""Génère les icônes PWA à partir du logo principal (PNG).

Usage :
    python scripts/generate_pwa_icons.py

Le script lit `static/images/logo-kwalokwakole.png` (logo site) et produit :
  - icon-192.png, icon-512.png, apple-touch-icon.png : logo sur fond **transparent**
    (adapté à l’écran d’accueil : le pictogramme seul, sans grand carré orange plein).
  - icon-maskable-512.png : même principe avec marge de sécurité (zone masquable).
  - favicon-32.png : petit favicon transparent.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "static" / "images" / "logo-kwalokwakole.png"
OUT_DIR = ROOT / "static" / "images" / "icons"


def _load_rgba() -> Image.Image:
    return Image.open(SRC).convert("RGBA")


def _icon_on_transparent(src: Image.Image, size: int, margin_ratio: float = 0.10) -> Image.Image:
    """Logo centré sur fond transparent (pas de fond orange plein écran)."""
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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    logo = _load_rgba()

    _icon_on_transparent(logo, 192, margin_ratio=0.10).save(OUT_DIR / "icon-192.png", "PNG")
    _icon_on_transparent(logo, 512, margin_ratio=0.10).save(OUT_DIR / "icon-512.png", "PNG")
    _icon_on_transparent(logo, 512, margin_ratio=0.22).save(OUT_DIR / "icon-maskable-512.png", "PNG")
    _icon_on_transparent(logo, 180, margin_ratio=0.10).save(OUT_DIR / "apple-touch-icon.png", "PNG")
    _transparent_favicon(logo, 32).save(OUT_DIR / "favicon-32.png", "PNG")

    print("Icônes PWA générées (fond transparent) dans", OUT_DIR)


if __name__ == "__main__":
    main()

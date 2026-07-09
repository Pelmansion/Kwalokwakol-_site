#!/usr/bin/env python
"""Applique le logo officiel et kolêgroup.com sur les affiches d'origine."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LOGO_PATH = ROOT / "static" / "images" / "logo-kwalokwakole.png"
OUT_DIR = ROOT / "docs" / "affiches"
SITE_URL = "kolêgroup.com"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    paths = (
        ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"]
        if bold
        else ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
    )
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def load_logo(max_height: int) -> Image.Image:
    logo = Image.open(LOGO_PATH).convert("RGBA")
    px = logo.load()
    for y in range(logo.height):
        for x in range(logo.width):
            r, g, b, a = px[x, y]
            if r < 45 and g < 45 and b < 45:
                px[x, y] = (r, g, b, 0)
    bbox = logo.getbbox()
    if bbox:
        logo = logo.crop(bbox)
    ratio = max_height / logo.height
    size = (max(1, int(logo.width * ratio)), max_height)
    return logo.resize(size, Image.Resampling.LANCZOS)


def cover_rect(img: Image.Image, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    ImageDraw.Draw(img).rectangle(box, fill=color)


def paste_logo(
    img: Image.Image,
    center: tuple[int, int],
    height: int,
    erase_box: tuple[int, int, int, int],
    *,
    fill: tuple[int, int, int] | None = None,
) -> None:
    x0, y0, x1, y1 = erase_box
    color = fill or img.getpixel(((x0 + x1) // 2, (y0 + y1) // 2))[:3]
    cover_rect(img, erase_box, color)
    logo = load_logo(height)
    cx, cy = center
    img.paste(logo, (cx - logo.width // 2, cy - logo.height // 2), logo)


def write_url(
    img: Image.Image,
    box: tuple[int, int, int, int],
    *,
    bg: tuple[int, int, int] | None,
    color: tuple[int, int, int],
    size: int,
    anchor: str = "mm",
    texture_from: tuple[int, int, int, int] | None = None,
    src: Image.Image | None = None,
) -> None:
    x0, y0, x1, y1 = box
    if texture_from and src is not None:
        patch = src.crop(texture_from).resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
        img.paste(patch, (x0, y0))
    elif bg is not None:
        cover_rect(img, box, bg)
    if anchor == "lm":
        pos = (box[0] + 6, (box[1] + box[3]) // 2)
    else:
        pos = ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2)
    ImageDraw.Draw(img).text(
        pos,
        SITE_URL,
        fill=color,
        font=_font(size, bold=True),
        anchor=anchor,
    )


# Calibrage fin — remplace uniquement le carré « K » et le texte d'URL
PATCHES: dict[str, dict] = {
    "affiche-pub-kole-group.png": {
        "logos": [
            {
                "center": (768, 102),
                "height": 88,
                "erase": (696, 38, 840, 170),
                "fill": (253, 245, 233),
            }
        ],
        "urls": [
            {
                "box": (1120, 952, 1292, 970),
                "texture_from": (200, 900, 360, 922),
                "color": (255, 255, 255),
                "size": 19,
                "anchor": "lm",
            }
        ],
    },
    "affiche-fonctionnement-vue-ensemble.png": {
        "logos": [{"center": (768, 78), "height": 62, "erase": (738, 48, 798, 108)}],
        "urls": [{"box": (610, 972, 926, 1012), "bg": (45, 28, 16), "color": (255, 255, 255), "size": 28}],
    },
    "affiche-fonctionnement-profils.png": {
        "logos": [{"center": (92, 982), "height": 46, "erase": (62, 952, 122, 1012)}],
        "urls": [{"box": (1210, 972, 1445, 1006), "bg": (45, 28, 16), "color": (255, 255, 255), "size": 22}],
    },
    "affiche-fonctionnement-client.png": {
        "logos": [
            {"center": (752, 76), "height": 58, "erase": (722, 46, 782, 106)},
            {"center": (1418, 986), "height": 34, "erase": (1398, 966, 1438, 1006)},
        ],
        "urls": [{"box": (938, 888, 1178, 922), "bg": (194, 65, 12), "color": (255, 255, 255), "size": 26}],
    },
    "affiche-fonctionnement-vendeur-prestataire.png": {
        "logos": [{"center": (108, 78), "height": 58, "erase": (78, 48, 138, 108)}],
        "urls": [{"box": (1070, 968, 1290, 1000), "bg": (61, 36, 20), "color": (255, 255, 255), "size": 22}],
    },
    "affiche-fonctionnement-culture.png": {
        "logos": [{"center": (102, 72), "height": 52, "erase": (72, 42, 132, 102)}],
        "urls": [
            {
                "box": (858, 930, 952, 954),
                "texture_from": (1005, 928, 1055, 952),
                "color": (255, 255, 255),
                "size": 26,
                "anchor": "lm",
            }
        ],
    },
}


def patch_poster(name: str) -> Path:
    path = OUT_DIR / name
    img = Image.open(path).convert("RGB")
    original = img.copy()
    cfg = PATCHES[name]
    for logo in cfg.get("logos", []):
        paste_logo(
            img,
            logo["center"],
            logo["height"],
            logo["erase"],
            fill=logo.get("fill"),
        )
    for url in cfg.get("urls", []):
        write_url(
            img,
            url["box"],
            bg=url.get("bg"),
            color=url["color"],
            size=url["size"],
            anchor=url.get("anchor", "mm"),
            texture_from=url.get("texture_from"),
            src=original,
        )
    img.save(path, "PNG", optimize=True)
    return path


def main() -> None:
    for name in PATCHES:
        print(f"OK  {patch_poster(name)}")
    pub_copy = ROOT / "docs" / "affiche-pub-kole-group.png"
    pub_copy.write_bytes((OUT_DIR / "affiche-pub-kole-group.png").read_bytes())
    print(f"OK  {pub_copy}")


if __name__ == "__main__":
    main()

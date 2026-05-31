#!/usr/bin/env python
"""Vérifie la configuration médias (local / R2 / disque Render)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kwalo.settings")

import django

django.setup()

from django.conf import settings
from django.core.files.storage import default_storage


def main() -> int:
    backend = settings.STORAGES["default"]["BACKEND"]
    cloud = getattr(settings, "USE_CLOUD_MEDIA", False)
    on_render = bool(os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME"))

    print("=== Configuration médias Kolê ===")
    print(f"  Backend      : {backend}")
    print(f"  MEDIA_URL    : {settings.MEDIA_URL}")
    print(f"  MEDIA_ROOT   : {settings.MEDIA_ROOT}")
    print(f"  Cloud (R2/S3): {'oui' if cloud else 'non'}")
    print(f"  Render       : {'oui' if on_render else 'non'}")

    if cloud:
        bucket = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")
        domain = os.environ.get("AWS_S3_CUSTOM_DOMAIN", "") or os.environ.get(
            "AWS_S3_PUBLIC_BASE_URL", ""
        )
        print(f"  Bucket       : {bucket}")
        print(f"  URL publique : {domain or '(à définir — images peut-être inaccessibles)'}")
        if not domain:
            print(
                "\n[!] Ajoutez AWS_S3_CUSTOM_DOMAIN=pub-xxxxx.r2.dev "
                "(Cloudflare R2 -> bucket -> Public access)."
            )
            return 1
        print("\n[OK] Stockage cloud configure.")
        return 0

    if on_render:
        root = str(settings.MEDIA_ROOT)
        if root.startswith("/data"):
            print("\n[OK] Disque persistant Render (MEDIA_ROOT=/data/...).")
            return 0
        print(
            "\n[ERREUR] SUR RENDER : les uploads dans media/ sont EFFACES a chaque deploy.\n"
            "  -> Configurez Cloudflare R2 (voir docs/RENDER_MEDIAS.md)\n"
            "  -> ou MEDIA_ROOT=/data/media + disque Render payant"
        )
        return 1

    print("\n[OK] Mode local (dossier media/).")
    try:
        default_storage.get_available_name("_healthcheck.txt")
    except Exception as exc:
        print(f"[!] Stockage : {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

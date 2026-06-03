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


_AWS_VARS = (
    "AWS_STORAGE_BUCKET_NAME",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_S3_ENDPOINT_URL",
    "AWS_S3_REGION_NAME",
    "AWS_S3_CUSTOM_DOMAIN",
    "AWS_LOCATION",
)


def _print_aws_env_status() -> None:
    print("\n--- Variables AWS_* vues par ce shell ---")
    for name in _AWS_VARS:
        raw = os.environ.get(name)
        if not raw:
            print(f"  {name}: (absente ou vide)")
        elif "SECRET" in name or "KEY" in name and name != "AWS_S3_CUSTOM_DOMAIN":
            print(f"  {name}: definie ({len(raw)} caracteres)")
        else:
            print(f"  {name}: {raw.strip()}")
    bucket = (os.environ.get("AWS_STORAGE_BUCKET_NAME") or "").strip()
    key = (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip()
    secret = (os.environ.get("AWS_SECRET_ACCESS_KEY") or "").strip()
    if not bucket:
        print(
            "\nCause probable : AWS_STORAGE_BUCKET_NAME manquant sur CE service web, "
            "ou redeploiement pas encore fait apres ajout des variables."
        )
    elif not key or not secret:
        print("\nCause probable : cles API R2 incomplètes (ID ou secret manquant).")


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
        _print_aws_env_status()
        return 1

    print("\n[OK] Mode local (dossier media/).")
    try:
        default_storage.get_available_name("_healthcheck.txt")
    except Exception as exc:
        print(f"[!] Stockage : {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

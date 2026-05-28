"""Configuration des fichiers uploadés (photos, audio, KYC…).

En local : dossier ``media/`` à la racine du projet.
En production Render :
  - disque persistant : variable ``MEDIA_ROOT=/chemin/monté`` (Render Disk) ;
  - ou stockage cloud S3 / Cloudflare R2 : variables ``AWS_STORAGE_BUCKET_NAME``, etc.
"""

from __future__ import annotations

import os
from pathlib import Path


def configure_media(
    *,
    base_dir: Path,
    debug: bool,
    installed_apps: list[str],
) -> dict:
    """Retourne MEDIA_URL, MEDIA_ROOT, STORAGES (clé default + staticfiles géré ailleurs)."""

    media_url = "/media/"
    media_root = Path(
        os.environ.get("MEDIA_ROOT", "").strip() or str(base_dir / "media")
    )

    default_storage = {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": str(media_root),
            "base_url": media_url,
        },
    }

    bucket = (os.environ.get("AWS_STORAGE_BUCKET_NAME") or "").strip()
    if bucket:
        if "storages" not in installed_apps:
            installed_apps.append("storages")

        endpoint = (os.environ.get("AWS_S3_ENDPOINT_URL") or "").strip() or None
        custom_domain = (os.environ.get("AWS_S3_CUSTOM_DOMAIN") or "").strip() or None
        region = (os.environ.get("AWS_S3_REGION_NAME") or "auto").strip()

        s3_options = {
            "bucket_name": bucket,
            "access_key": (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip(),
            "secret_key": (os.environ.get("AWS_SECRET_ACCESS_KEY") or "").strip(),
            "region_name": region,
            "default_acl": "public-read",
            "file_overwrite": False,
            "querystring_auth": False,
        }
        if endpoint:
            s3_options["endpoint_url"] = endpoint
        if custom_domain:
            s3_options["custom_domain"] = custom_domain
            media_url = f"https://{custom_domain.rstrip('/')}/"
        elif endpoint and bucket:
            # URL publique type R2 sans domaine personnalisé
            media_url = f"{endpoint.rstrip('/')}/{bucket}/"

        default_storage = {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": s3_options,
        }

    return {
        "MEDIA_URL": media_url,
        "MEDIA_ROOT": media_root,
        "STORAGES_DEFAULT": default_storage,
        "USE_CLOUD_MEDIA": bool(bucket),
    }

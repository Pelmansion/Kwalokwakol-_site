"""Configuration des fichiers uploadés (photos, audio, KYC…).

En local : dossier ``media/`` à la racine du projet.
En production Render (disque éphémère) :
  - **Recommandé** : Cloudflare R2 (variables AWS_* ci-dessous) ;
  - **Alternative** : disque persistant Render + ``MEDIA_ROOT=/data/media``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def _is_render() -> bool:
    return bool((os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME") or "").strip())


def configure_media(
    *,
    base_dir: Path,
    debug: bool,
    installed_apps: list[str],
) -> dict:
    """Retourne MEDIA_URL, MEDIA_ROOT, STORAGES default, USE_CLOUD_MEDIA."""

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
    use_cloud = False

    bucket = (os.environ.get("AWS_STORAGE_BUCKET_NAME") or "").strip()
    access_key = (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip()
    secret_key = (os.environ.get("AWS_SECRET_ACCESS_KEY") or "").strip()

    if bucket:
        if not access_key or not secret_key:
            raise RuntimeError(
                "AWS_STORAGE_BUCKET_NAME est défini mais AWS_ACCESS_KEY_ID ou "
                "AWS_SECRET_ACCESS_KEY manque. Les uploads échoueront sur Render."
            )

        if "storages" not in installed_apps:
            installed_apps.append("storages")

        endpoint = (os.environ.get("AWS_S3_ENDPOINT_URL") or "").strip() or None
        custom_domain = (os.environ.get("AWS_S3_CUSTOM_DOMAIN") or "").strip() or None
        public_base = (os.environ.get("AWS_S3_PUBLIC_BASE_URL") or "").strip().rstrip("/")
        region = (os.environ.get("AWS_S3_REGION_NAME") or "auto").strip()
        location = (os.environ.get("AWS_LOCATION") or "media").strip().strip("/")

        s3_options: dict = {
            "bucket_name": bucket,
            "access_key": access_key,
            "secret_key": secret_key,
            "region_name": region,
            "file_overwrite": False,
            "querystring_auth": False,
            "default_acl": None,
            "addressing_style": "path",
        }
        if location:
            s3_options["location"] = location
        if endpoint:
            s3_options["endpoint_url"] = endpoint
        if custom_domain:
            s3_options["custom_domain"] = custom_domain.lstrip("https://").lstrip("http://").rstrip("/")

        if public_base:
            media_url = f"{public_base}/"
        elif custom_domain:
            media_url = f"https://{s3_options['custom_domain']}/"
            if location:
                media_url = f"{media_url}{location}/"
        elif endpoint:
            # Fallback — souvent non public ; préférer AWS_S3_CUSTOM_DOMAIN (pub-xxx.r2.dev)
            media_url = f"{endpoint.rstrip('/')}/{bucket}/"
            if location:
                media_url = f"{media_url}{location}/"
            logger.warning(
                "Médias R2/S3 : définissez AWS_S3_CUSTOM_DOMAIN (ex. pub-xxx.r2.dev) "
                "ou AWS_S3_PUBLIC_BASE_URL pour des URLs d'images accessibles."
            )

        default_storage = {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": s3_options,
        }
        use_cloud = True

    elif _is_render() and not debug:
        persistent = str(media_root).startswith("/data")
        if not persistent:
            logger.warning(
                "RENDER sans stockage cloud (R2/S3) : les images uploadées seront "
                "perdues à chaque redéploiement. Ajoutez AWS_STORAGE_BUCKET_NAME + clés "
                "ou un disque persistant MEDIA_ROOT=/data/media."
            )

    return {
        "MEDIA_URL": media_url,
        "MEDIA_ROOT": media_root,
        "STORAGES_DEFAULT": default_storage,
        "USE_CLOUD_MEDIA": use_cloud,
    }

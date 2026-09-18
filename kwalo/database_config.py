"""Résolution de DATABASE_URL (Render, Heroku, local)."""

from __future__ import annotations

import os
from urllib.parse import quote_plus

# Noms d'environnement possibles selon l'hébergeur / le dashboard Render.
_URL_KEYS = (
    "DATABASE_URL",
    "POSTGRES_URL",
    "KOLE_DATABASE_URL",
    "RENDER_DATABASE_URL",
    "INTERNAL_DATABASE_URL",
    "EXTERNAL_DATABASE_URL",
)


def _first_env(*keys: str) -> str:
    for key in keys:
        value = (os.environ.get(key) or "").strip()
        if value:
            return value
    return ""


def _build_from_pg_vars() -> str:
    user = _first_env("PGUSER", "POSTGRES_USER")
    password = _first_env("PGPASSWORD", "POSTGRES_PASSWORD")
    host = _first_env("PGHOST", "POSTGRES_HOST")
    port = _first_env("PGPORT", "POSTGRES_PORT") or "5432"
    name = _first_env("PGDATABASE", "POSTGRES_DB", "POSTGRES_DATABASE")
    if not all((user, password, host, name)):
        return ""
    return (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )


def resolve_database_url() -> str:
    """Retourne l'URL PostgreSQL la plus fiable disponible."""
    for key in _URL_KEYS:
        value = (os.environ.get(key) or "").strip()
        if value:
            return value
    return _build_from_pg_vars()


def ensure_database_url_env() -> str:
    """Exporte DATABASE_URL dans os.environ si trouvée autrement."""
    url = resolve_database_url()
    if url:
        os.environ["DATABASE_URL"] = url
    return url


def postgres_ssl_required(database_url: str, *, debug: bool) -> bool:
    """SSL requis pour Postgres externe ; pas pour l'URL interne Render."""
    if debug:
        return False
    url = (database_url or "").lower()
    if "sslmode=disable" in url or "sslmode=allow" in url:
        return False
    if "@" in url:
        host_part = url.split("@", 1)[1].split("/", 1)[0].split("?", 1)[0]
        # Hôte interne Render (réseau privé, sans *.render.com).
        if ".render.com" not in host_part:
            return False
    return True

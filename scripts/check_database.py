#!/usr/bin/env python
"""Refuse SQLite en production — Render doit utiliser PostgreSQL (DATABASE_URL)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kwalo.ensure_settings import ensure_settings_module

ensure_settings_module()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kwalo.settings")

import django

django.setup()

from django.conf import settings

engine = settings.DATABASES["default"]["ENGINE"]
on_render = bool(os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME"))

print("=== Vérification base de données ===")
print(f"  ENGINE : {engine}")
print(f"  Render : {'oui' if on_render else 'non'}")

if "sqlite" in engine and (on_render or not settings.DEBUG):
    print(
        "\nERREUR: Django utilise SQLite au lieu de PostgreSQL.\n"
        "  → Render : Web Service → Environment → DATABASE_URL\n"
        "  → PostgreSQL → Connect → lier la base au service web\n"
        "  → Manual Deploy après avoir enregistré la variable.",
        file=sys.stderr,
    )
    sys.exit(1)

if "postgresql" not in engine and (on_render or not settings.DEBUG):
    print(f"\nERREUR: moteur inattendu en production ({engine}).", file=sys.stderr)
    sys.exit(1)

print("  OK : PostgreSQL actif")

#!/usr/bin/env python
"""Vérifie que les templates de widgets existent (évite les 500 en prod)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
if not os.environ.get("DATABASE_URL"):
    os.environ["DEBUG"] = "true"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kwalo.settings")

import django

django.setup()

from django.template.loader import get_template

REQUIRED = [
    "django/forms/widgets/text.html",
    "django/forms/widgets/select.html",
    "django/forms/widgets/checkbox.html",
    "django/forms/widgets/textarea.html",
    "django/forms/widgets/date.html",
    "django/forms/widgets/time.html",
    "django/forms/widgets/file.html",
    "django/forms/widgets/clearable_file_input.html",
    "culture/widgets/featured_artists_widget.html",
    "culture/widgets/split_datetime_widget.html",
]

failed = []
for name in REQUIRED:
    try:
        get_template(name)
    except Exception as exc:
        failed.append((name, exc))

if failed:
    for name, exc in failed:
        print(f"MISSING {name}: {exc}", file=sys.stderr)
    sys.exit(1)

print("Form templates OK")

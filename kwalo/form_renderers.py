"""
Renderer de formulaires : templates projet (culture/widgets) + widgets Django intégrés.
Évite TemplateDoesNotExist (ex. django/forms/widgets/text.html) en production.
"""

from __future__ import annotations

from pathlib import Path

import django
from django.conf import settings
from django.forms.renderers import TemplatesSetting
from django.template.backends.django import DjangoTemplates
from django.template.utils import get_app_template_dirs


class KwaloFormRenderer(TemplatesSetting):
    """Moteur de templates dédié aux formulaires avec les deux répertoires requis."""

    def get_template(self, template_name):
        backend = DjangoTemplates(
            {
                "DIRS": self._form_template_dirs(),
                "APP_DIRS": True,
                "NAME": "djangoforms",
                "OPTIONS": {},
            }
        )
        return backend.get_template(template_name)

    @staticmethod
    def _form_template_dirs():
        base = Path(settings.BASE_DIR)
        django_forms = Path(django.__file__).resolve().parent / "forms" / "templates"
        dirs = [base / "templates", django_forms]
        for p in get_app_template_dirs("templates"):
            if p not in dirs:
                dirs.append(p)
        return dirs

"""
WSGI config for kwalo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from kwalo.database_config import ensure_database_url_env
from kwalo.ensure_settings import ensure_settings_module

ensure_database_url_env()
ensure_settings_module()

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kwalo.settings')

application = get_wsgi_application()

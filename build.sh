#!/usr/bin/env bash
# Commande de build Render (ou autre PaaS) — à configurer dans le tableau de bord.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py sync_static_pages
python scripts/check_form_templates.py
python scripts/check_media_config.py || true

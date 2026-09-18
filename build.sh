#!/usr/bin/env bash
# Commande de build Render (ou autre PaaS) — à configurer dans le tableau de bord.
set -o errexit

# settings.py n'est pas versionné : généré depuis le modèle pour le déploiement.
if [ ! -f kwalo/settings.py ]; then
  cp kwalo/settings.example.py kwalo/settings.py
  echo "==> kwalo/settings.py créé depuis settings.example.py"
fi

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py sync_static_pages
python scripts/check_form_templates.py
python scripts/check_media_config.py || true

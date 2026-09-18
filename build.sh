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
python scripts/check_form_templates.py
python scripts/check_media_config.py || true

if [ -n "${DATABASE_URL:-}" ]; then
  echo "==> Migrations (build, DATABASE_URL presente)..."
  python manage.py migrate --noinput
else
  echo "==> DATABASE_URL absente au build — migrations au demarrage (start.sh)."
fi

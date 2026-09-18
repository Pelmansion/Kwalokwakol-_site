#!/usr/bin/env bash
# Commande de build Render (ou autre PaaS) — à configurer dans le tableau de bord.
set -o errexit

# settings.py n'est pas versionné : généré depuis le modèle pour le déploiement.
if [ ! -f kwalo/settings.py ]; then
  cp kwalo/settings.example.py kwalo/settings.py
  echo "==> kwalo/settings.py créé depuis settings.example.py"
fi

pip install -r requirements.txt

# collectstatic sans PostgreSQL ; SQLite temporaire autorisé
export RENDER_ALLOW_SQLITE_BUILD=1
python manage.py collectstatic --noinput
unset RENDER_ALLOW_SQLITE_BUILD

python scripts/check_form_templates.py
python scripts/check_media_config.py || true

if [ -n "${DATABASE_URL:-}" ]; then
  echo "==> Migrations (build, DATABASE_URL presente)..."
  python manage.py migrate --noinput
fi

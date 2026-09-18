#!/usr/bin/env bash
# Commande de build Render (ou autre PaaS) — à configurer dans le tableau de bord.
set -o errexit

# settings.py n'est pas versionné : toujours synchronisé depuis le modèle (évite cache Render obsolète).
cp kwalo/settings.example.py kwalo/settings.py
echo "==> kwalo/settings.py synchronisé depuis settings.example.py"

pip install -r requirements.txt

if [ -n "${RENDER:-}${RENDER_EXTERNAL_HOSTNAME:-}" ] && [ -z "${DATABASE_URL:-}" ]; then
  echo "ERREUR: DATABASE_URL absent sur Render (build)."
  echo "Liez PostgreSQL au Web Service avant de deployer."
  exit 1
fi

if [ -n "${DATABASE_URL:-}" ]; then
  python scripts/check_database.py
fi

python manage.py collectstatic --noinput
python scripts/check_form_templates.py
python scripts/check_media_config.py || true

if [ -n "${DATABASE_URL:-}" ]; then
  echo "==> Migrations (build, DATABASE_URL presente)..."
  python manage.py migrate --noinput
else
  echo "==> DATABASE_URL absente au build — migrations au demarrage (start.sh)."
fi

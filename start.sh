#!/usr/bin/env bash
# Commande de démarrage Render — migrations à chaque lancement, puis Gunicorn.
set -o errexit

if [ ! -f kwalo/settings.py ]; then
  cp kwalo/settings.example.py kwalo/settings.py
  echo "==> kwalo/settings.py créé depuis settings.example.py"
fi

if [ -n "${RENDER:-}" ] || [ -n "${RENDER_EXTERNAL_HOSTNAME:-}" ]; then
  if [ -z "${DATABASE_URL:-}" ]; then
    echo "ERREUR: DATABASE_URL est absent."
    echo "Render → votre base PostgreSQL → Connect → choisissez ce service web."
    echo "Ou ajoutez DATABASE_URL manuellement dans Environment."
    exit 1
  fi
fi

# Dossier des fichiers uploadés (disque Render ou media/ local)
MEDIA_DIR="${MEDIA_ROOT:-media}"
mkdir -p "$MEDIA_DIR"
echo "==> Dossier médias prêt : $MEDIA_DIR"

echo "==> Migrations base de données..."
python manage.py migrate --noinput

echo "==> Pages statiques (FAQ, CGU, contact)..."
python manage.py sync_static_pages

echo "==> Démarrage Gunicorn sur le port ${PORT:-8000}..."
exec gunicorn kwalo.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers 2 \
  --threads 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -

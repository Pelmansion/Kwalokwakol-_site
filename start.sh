#!/usr/bin/env bash
# Commande de démarrage Render — migrations à chaque lancement, puis Gunicorn.
set -o errexit

# Dossier des fichiers uploadés (disque Render ou media/ local)
MEDIA_DIR="${MEDIA_ROOT:-media}"
mkdir -p "$MEDIA_DIR"
echo "==> Dossier médias prêt : $MEDIA_DIR"

echo "==> Migrations base de données..."
python manage.py migrate --noinput

echo "==> Démarrage Gunicorn sur le port ${PORT:-8000}..."
exec gunicorn kwalo.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers 2 \
  --threads 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -

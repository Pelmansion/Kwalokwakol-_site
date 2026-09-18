# Déploiement Render — Kolê Group

## Erreur `npm ENOENT package.json`

Render essaie de builder en **Node.js** alors que ce projet est **Django (Python)**.

Dans **Render → votre service → Settings** :

| Paramètre | Valeur |
|-----------|--------|
| **Runtime** | `Python 3` |
| **Build Command** | `bash build.sh` |
| **Start Command** | `bash start.sh` |
| **Root Directory** | *(vide — racine du dépôt)* |

Ne pas utiliser `npm install` ni `npm run build` : il n’y a pas de `package.json` à la racine (le frontend React est optionnel dans `frontend/`).

## Variables d'environnement obligatoires

- `SECRET_KEY` — clé Django (générée par Render ou manuelle)
- `DEBUG` — `false`
- `DATABASE_URL` — URL PostgreSQL Render
- `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` — Gmail (mot de passe d'application)
- `GENIUS_API_KEY` / `GENIUS_API_SECRET` — paiements

## Fichier settings.py

`kwalo/settings.py` **n'est pas poussé sur Git** (secrets locaux).

- **Local :** `copy kwalo\settings.example.py kwalo\settings.py` puis éditer
- **Render :** `build.sh` copie automatiquement `settings.example.py` → `settings.py`

## Dépôt Git

Projet lié à : https://github.com/pelmansions-ux/KOLEGROUP

# Déploiement Render — Kolê Group

## Erreur `npm ENOENT package.json`

Render essaie de builder en **Node.js**. Deux solutions :

### Option A — Recommandée : Python 3

Dans **Render → votre service → Settings** :

| Paramètre | Valeur |
|-----------|--------|
| **Runtime** | `Python 3` |
| **Build Command** | `bash build.sh` |
| **Start Command** | `bash start.sh` |
| **Root Directory** | *(vide — racine du dépôt)* |

### Option B — Si Render reste en Node.js

Un `package.json` à la racine délègue à Django :

| Paramètre | Valeur |
|-----------|--------|
| **Runtime** | `Node` |
| **Build Command** | `npm install` |
| **Start Command** | `npm start` |

`npm install` exécute `build.sh` (pip, migrate, collectstatic…).  
`npm start` lance Gunicorn via `start.sh`.

**Ne pas** utiliser `npm run build` seul sans `npm install`.

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

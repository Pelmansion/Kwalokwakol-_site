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

## Lier la base PostgreSQL (obligatoire)

Sans `DATABASE_URL`, le **build** peut passer mais le **démarrage** échouera.

1. Render → **PostgreSQL** (ex. `kwalokwakole`)
2. Onglet **Connect** → **Add connection** → sélectionnez votre **Web Service**
3. Render ajoute automatiquement `DATABASE_URL` dans Environment
4. **Redéployez** le service web

Vérifiez dans **Environment** que `DATABASE_URL` commence par `postgresql://`.

## Variables d'environnement obligatoires

- `SECRET_KEY` — clé Django (générée par Render ou manuelle)
- `DEBUG` — `false`
- `DATABASE_URL` — URL PostgreSQL Render (via Connect)
- `PYTHON_VERSION` — `3.12.3` (évite Python 3.14 instable)
- `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` — Gmail (mot de passe d'application)
- `GENIUS_API_KEY` / `GENIUS_API_SECRET` — paiements

## Fichier settings.py

`kwalo/settings.py` **n'est pas poussé sur Git** (secrets locaux).

- **Local :** `copy kwalo\settings.example.py kwalo\settings.py` puis éditer
- **Render :** `build.sh` copie automatiquement `settings.example.py` → `settings.py`

## Dépôt Git

Projet lié à : https://github.com/pelmansions-ux/KOLEGROUP

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

## Erreur « DATABASE_URL est absent » (démarrage)

Le **build réussit** mais le site **ne démarre pas** : le service web n'a pas accès à PostgreSQL.

### Méthode 1 — Lier la base (recommandé)

1. [Render Dashboard](https://dashboard.render.com) → cliquez sur votre base **PostgreSQL** (ex. `kwalokwakole`)
2. Menu **Connect** (ou **Info**)
3. Section **Connections** → **Add connection**
4. Choisissez votre **Web Service** (pas la base elle-même)
5. Validez → Render crée `DATABASE_URL` sur le **service web**
6. Ouvrez le **Web Service** → **Environment** → vérifiez que `DATABASE_URL` apparaît (`postgresql://…`)
7. **Manual Deploy** sur le service web

### Méthode 2 — Coller l'URL à la main

1. Base PostgreSQL → **Connect** → copiez **Internal Database URL**
2. Web Service → **Environment** → **Add Environment Variable**
   - Key : `DATABASE_URL`
   - Value : l'URL copiée
3. **Save** puis **Manual Deploy**

> La variable doit être sur le **Web Service**, pas seulement sur la base de données.

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

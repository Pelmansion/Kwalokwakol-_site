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

1. Base PostgreSQL → **Connect**
2. Copiez **Internal Database URL** (recommandé, même réseau Render)
   - ou **External Database URL** si le service est ailleurs
3. **Web Service** → **Environment** → **Add Environment Variable**
   - Key : `DATABASE_URL`
   - Value : l'URL `postgresql://...` (sans espaces)
4. **Save Changes** puis **Manual Deploy**

> La variable doit être sur le **Web Service**, pas seulement sur la base PostgreSQL.
> Sans `DATABASE_URL` sur le service web, le build peut réussir mais le site plantera au démarrage.

## Variables d'environnement obligatoires

- `SECRET_KEY` — clé Django (générée par Render ou manuelle)
- `DEBUG` — `false`
- `DATABASE_URL` — URL PostgreSQL Render (via Connect)
- `PYTHON_VERSION` — `3.12.3` (évite Python 3.14 instable)
- `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` — Gmail (mot de passe d'application)
- `GENIUS_API_KEY` / `GENIUS_API_SECRET` — paiements

## Fichier settings.py (normal qu'il ne soit pas sur Git)

| Fichier | Sur GitHub ? | Rôle |
|---------|--------------|------|
| `kwalo/settings.example.py` | **Oui** | Modèle sans secrets |
| `kwalo/settings.py` | **Non** (`.gitignore`) | Votre config locale avec mots de passe |

- **Local :** `copy kwalo\settings.example.py kwalo\settings.py` puis éditer
- **Render :** `build.sh` / `start.sh` copient `settings.example.py` → `settings.py` au déploiement

## Erreur 500 (Internal Server Error) en production

Si `/hors-ligne/` fonctionne mais `/`, `/produits/` ou `/compte/connexion/` renvoient une page « Oups, une erreur est survenue » :

1. **Vérifiez `DATABASE_URL`** sur le **Web Service** (Environment), pas seulement sur la base PostgreSQL.
2. **Redéployez** après mise à jour du code (`build.sh` / `start.sh` resynchronisent `settings.py` à chaque déploiement).
3. **AWS / R2** : soit toutes les variables (`AWS_STORAGE_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_CUSTOM_DOMAIN`), soit **aucune** (ne laissez pas le bucket seul).
4. Consultez les **logs Render** au moment d'une requête en erreur : le middleware journalise la traceback complète.

## Message AWS_STORAGE_BUCKET_NAME (build)

Ce message vient de `check_media_config.py` pendant le build. **Il n'empêche pas le build** (avertissement).

Pour conserver les **images uploadées** sur Render gratuit, ajoutez Cloudflare R2 dans **Environment** :

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_STORAGE_BUCKET_NAME`
- `AWS_S3_ENDPOINT_URL`
- `AWS_S3_CUSTOM_DOMAIN`
- `AWS_S3_REGION_NAME` = `auto`

Guide : `docs/RENDER_MEDIAS.md`. Sans R2, le site fonctionne mais les uploads sont effacés à chaque deploy.

## Dépôt Git

Projet lié à : https://github.com/Pelmansion/Kwalokwakol-_site

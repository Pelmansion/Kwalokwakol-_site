# Images et fichiers sur Render (Kolê)

## Pourquoi les images disparaissent

Sur Render **gratuit**, le disque du serveur est **temporaire**. Chaque redéploiement efface le dossier `media/`.  
La base garde le chemin (`/media/avatars/photo.jpg`) mais le fichier n’existe plus → image cassée.

## Solution recommandée : Cloudflare R2 (gratuit au départ)

### 1. Créer le bucket

1. [dash.cloudflare.com](https://dash.cloudflare.com) → **R2** → **Create bucket** (ex. `kole-media`)
2. **Settings** → **Public access** → activer l’URL publique `https://pub-xxxxx.r2.dev`

### 2. Token API

**R2** → **Manage R2 API Tokens** → Create → Read & Write sur le bucket.

Notez :

- Access Key ID  
- Secret Access Key  
- Account ID (pour l’endpoint)

### 3. Variables sur Render

Service web → **Environment** :

| Variable | Exemple |
|----------|---------|
| `AWS_ACCESS_KEY_ID` | (token) |
| `AWS_SECRET_ACCESS_KEY` | (secret) |
| `AWS_STORAGE_BUCKET_NAME` | `kole-media` |
| `AWS_S3_ENDPOINT_URL` | `https://VOTRE_ACCOUNT_ID.r2.cloudflarestorage.com` |
| `AWS_S3_REGION_NAME` | `auto` |
| `AWS_S3_CUSTOM_DOMAIN` | `pub-xxxxx.r2.dev` |
| `AWS_LOCATION` | `media` (optionnel, dossier dans le bucket) |

**Important :** `AWS_S3_CUSTOM_DOMAIN` doit être le domaine **public** (`pub-….r2.dev`), pas l’endpoint S3 privé.

### 4. Redéployer

Après **Save**, lancez un deploy. Puis **re-téléversez** les images (profil, produits, culture…) : les anciens fichiers perdus ne reviennent pas seuls.

### 5. Vérifier

Shell Render :

```bash
python scripts/check_media_config.py
```

Doit afficher `Cloud (R2/S3): oui` et l’URL publique.

---

## Alternative : disque persistant Render (payant)

1. Ajouter un **Disk** monté sur `/data/media`
2. Variable `MEDIA_ROOT=/data/media`
3. Pas besoin des variables `AWS_*`

---

## En local

Sans variables `AWS_*`, les fichiers vont dans le dossier `media/` à la racine du projet.
